import asyncio
import logging
from collections.abc import AsyncIterator, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import aiohttp

from wps_nwp._http import Transport
from wps_nwp.errors import FetchError, NotAvailable
from wps_nwp.field import Field, extract
from wps_nwp.models import MODELS, Model, Part
from wps_nwp.variables import Native, Variable

logger = logging.getLogger(__name__)


class Client:
    """
    Fetches model fields over HTTP. Nothing is written to disk.

        async with Client() as client:
            run = await client.latest_run("ifs")
            fields = await client.fetch("ifs", run, steps=[0, 3, 6], variables=["t2m", "precip"])

    Only the bytes of the requested fields are downloaded, concurrently, from the first of
    the model's mirrors that has them. For a whole run, stream does the same without holding
    every field in memory at once.
    """

    def __init__(
        self,
        *,
        concurrency: int = 16,
        timeout: float = 20.0,
        retries: int = 3,
        backoff: float = 1.0,
        session: aiohttp.ClientSession | None = None,
    ):
        """
        :param concurrency: maximum simultaneous connections to any one host
        :param timeout: seconds to wait for a connection, or for more data once connected
        :param retries: extra attempts for a request that times out or gets a 429 or 5xx
        :param backoff: seconds before the first retry; doubles on each one after
        :param session: use this session instead of creating one. The caller closes it, and
            its connector and timeouts replace concurrency and timeout.
        """
        self._http = Transport(
            concurrency=concurrency,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
            session=session,
        )

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    async def fetch(
        self,
        model: Model | str,
        run: datetime,
        steps: int | Iterable[int],
        variables: Variable | Native | str | Iterable[Variable | Native | str],
        *,
        skip_missing: bool = False,
    ) -> list[Field]:
        """
        Fetch variables for one or more forecast steps of a model run.

        :param model: a Model, or the name of a built-in one ("ifs", "gfs", "hrdps", ...)
        :param run: when the model run started. Naive datetimes are taken to be UTC.
        :param steps: forecast hours after run
        :param variables: Variable members or their names ("t2m"), or Native selectors
        :param skip_missing: leave out fields that are not published instead of raising
            NotAvailable. Whatever is missing is simply absent from the result.
        :return: fields ordered by step, then by variable, as requested
        :raises NotAvailable: a field is not published, unless skip_missing is set
        :raises FetchError: a field could not be retrieved from any mirror
        :raises ValueError: the model has no such variable or does not run at that hour
        """
        steps = [steps] if isinstance(steps, int) else list(dict.fromkeys(steps))
        by_step = {}
        async for fields in self.stream(
            model, run, steps, variables, skip_missing=skip_missing, window=max(1, len(steps))
        ):
            by_step[fields[0].step] = fields
        return [field for step in steps for field in by_step.get(step, [])]

    async def stream(
        self,
        model: Model | str,
        run: datetime,
        steps: int | Iterable[int],
        variables: Variable | Native | str | Iterable[Variable | Native | str],
        *,
        skip_missing: bool = False,
        window: int = 8,
    ) -> AsyncIterator[list[Field]]:
        """
        Fetch like fetch does, but hand over each step as soon as it has arrived.

            async for fields in client.stream("hrdps", run, range(1, 49), ["t2m", "precip"]):
                values = await sample(fields, lats, lons)

        Each item is one step's fields, ordered by variable. Steps come in the order they
        finish downloading, not the order requested. At most window steps are downloaded
        ahead of the caller, so memory stays flat however long the run is, where fetch holds
        every field at once. Arguments and errors are those of fetch.

        :param window: how many steps may be in flight or waiting to be handed over
        """
        model = _model(model)
        run = _run_time(model, run)
        steps = [steps] if isinstance(steps, int) else list(dict.fromkeys(steps))
        if isinstance(variables, (str, Native)):
            variables = [variables]
        variables = list(
            dict.fromkeys(v if isinstance(v, Native) else Variable(v) for v in variables)
        )
        for variable in variables:
            model.selector(variable)  # fail on unknown variables before making any request

        slots = asyncio.Semaphore(window)

        async def fetch_step(step: int) -> list[Field]:
            await slots.acquire()  # given back once the caller has finished with the step
            return await self._fetch_step(model, run, step, variables, skip_missing)

        tasks = {asyncio.ensure_future(fetch_step(step)) for step in steps}
        try:
            async for finished in asyncio.as_completed(tasks):
                # A finished task holds on to its result, so it must not be kept: dropping it
                # here is what lets a step's fields be freed once the caller is done with them.
                tasks.discard(finished)
                fields = finished.result()
                del finished
                if fields:
                    yield fields
                del fields
                slots.release()
        finally:
            # Reached on an error, or when the caller stops early: abandon what is left.
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def latest_run(
        self,
        model: Model | str,
        *,
        step: int = 0,
        now: datetime | None = None,
        lookback: timedelta = timedelta(days=2),
    ) -> datetime:
        """
        The most recent run of model that has published the given forecast step.

        Models publish a run's steps in order, so pass the last step you need to get a run
        that is complete as far as you are concerned.

        :raises NotAvailable: no run in the lookback period has published that step
        """
        model = _model(model)
        now = _utc(now) if now else datetime.now(UTC)
        run = now.replace(minute=0, second=0, microsecond=0)
        while now - run <= lookback:
            if run.hour in model.cycles and await self._published(model, run, step):
                return run
            run -= timedelta(hours=1)
        raise NotAvailable(f"{model.name}: no run since {now - lookback:%Y-%m-%d %H}Z has +{step}h")

    async def _published(self, model: Model, run: datetime, step: int) -> bool:
        failure = None
        for mirror in model.mirrors:
            try:
                if await self._http.exists(model.probe(mirror, run, step)):
                    return True
                failure = None
            except FetchError as error:
                failure = error
        if failure:
            raise failure
        return False

    async def _fetch_step(
        self,
        model: Model,
        run: datetime,
        step: int,
        variables: Sequence[Variable | Native],
        skip_missing: bool,
    ) -> list[Field]:
        found: dict[Variable | Native, Field] = {}
        # Why each variable is still outstanding, going by the last mirror that was asked:
        # a FetchError if that mirror failed, no entry if it simply does not have the data.
        errors: dict[Variable | Native, FetchError] = {}
        pending = list(variables)

        for mirror in model.mirrors:
            try:
                parts = await model.locate(self._http.get, mirror, run, step, pending)
            except NotAvailable:
                errors.clear()
                continue
            except FetchError as error:
                errors.update(dict.fromkeys(pending, error))
                continue

            requests = _plan(parts)
            outcomes = await asyncio.gather(
                *(self._download(request) for request in requests), return_exceptions=True
            )
            for request, outcome in zip(requests, outcomes):
                for part in request.parts:
                    errors.pop(part.variable, None)
                    if isinstance(outcome, FetchError):
                        errors[part.variable] = outcome
                    elif isinstance(outcome, BaseException) and not isinstance(
                        outcome, NotAvailable
                    ):
                        raise outcome
                if isinstance(outcome, list):
                    for part, grib in outcome:
                        found[part.variable] = Field(
                            model.name, part.variable, run, step, part.url, grib
                        )

            # A step that exists without a variable lacks it on every mirror, so only what
            # this mirror located and failed to deliver is worth asking the next one for.
            located = {part.variable for part in parts}
            for variable in pending:
                if variable not in located:
                    errors.pop(variable, None)
            pending = [v for v in pending if v in located and v not in found]
            if not pending:
                break

        missing = [v for v in variables if v not in found]
        for variable in missing:
            if variable in errors:
                raise errors[variable]
        if missing and not skip_missing:
            names = ", ".join(str(v) for v in missing)
            raise NotAvailable(f"{model.name} {run:%Y-%m-%d %H}Z +{step}h: no {names}")
        return [found[v] for v in variables if v in found]

    async def _download(self, request: "_Request") -> list[tuple[Part, bytes]]:
        length = None if request.end is None else request.end - request.offset
        body = await self._http.get(request.url, request.offset, length)
        try:
            return [
                (part, extract(_slice(body, part, request.offset), part.subfield))
                for part in request.parts
            ]
        except ValueError as error:
            raise FetchError(request.url, str(error)) from error


@dataclass
class _Request:
    """One HTTP request covering one or more parts of the same file."""

    url: str
    offset: int
    end: int | None  # None reads to the end of the file
    parts: list[Part]


def _plan(parts: Iterable[Part]) -> list[_Request]:
    """Group parts so that fields stored back to back, or in the same message, share a request."""
    requests: list[_Request] = []
    for part in sorted(parts, key=lambda p: (p.url, p.offset)):
        end = None if part.length is None else part.offset + part.length
        last = requests[-1] if requests else None
        if last and last.url == part.url and (last.end is None or part.offset <= last.end):
            if last.end is not None:
                last.end = None if end is None else max(last.end, end)
            last.parts.append(part)
        else:
            requests.append(_Request(part.url, part.offset, end, [part]))
    return requests


def _slice(body: bytes, part: Part, body_offset: int) -> bytes:
    start = part.offset - body_offset
    return body[start : None if part.length is None else start + part.length]


def _model(model: Model | str) -> Model:
    if isinstance(model, Model):
        return model
    try:
        return MODELS[model.lower()]
    except KeyError:
        raise ValueError(f"unknown model {model!r}; choose from {', '.join(MODELS)}") from None


def _utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def _run_time(model: Model, run: datetime) -> datetime:
    run = _utc(run)
    if run.hour not in model.cycles or run != run.replace(minute=0, second=0, microsecond=0):
        hours = ", ".join(f"{hour:02d}Z" for hour in model.cycles)
        raise ValueError(f"{model.name} runs at {hours}, not {run:%H:%M}Z")
    return run
