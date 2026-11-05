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

        Nothing is opened here. The HTTP session is created on the first request, because it
        has to be made inside a running event loop.
        """
        self._http = Transport(
            concurrency=concurrency,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
            session=session,
        )

    async def __aenter__(self) -> "Client":
        """Return the client itself. Connections are opened lazily, on the first request."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Close the client on leaving the async with block, whether or not it raised."""
        await self.close()

    async def close(self) -> None:
        """
        Close the HTTP session and its pooled connections.

        A session that was passed in to the constructor is left open for its owner to close.
        """
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

        How it works: this is stream with its window opened to the whole request. Every step
        is downloaded concurrently and collected as it finishes, keyed by its step, and the
        steps are then put back into the order asked for. A step repeated in steps is fetched
        once. A step that produced no fields, which can only happen with skip_missing,
        contributes nothing.
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

        How it works:

        1. The model, run time and variables are checked, so a bad request raises before
           anything is downloaded.
        2. One task is created per step, but each must take a slot from a semaphore of size
           window before it starts downloading. Slots are handed out in the order the steps
           were given.
        3. Steps are yielded as their tasks finish. A slot is only given back when the
           caller's loop comes back for the next item, which is what stops downloads running
           ahead of a slow caller.
        4. Each finished task is dropped as its step is yielded. A task keeps its result, so
           holding on to it would keep every step's GRIB alive until the end.
        5. If a step fails, its error is raised out of the caller's loop, after any steps
           that finished before it have been yielded.
        6. On an error, or when the caller stops early and the generator is closed, the tasks
           that are left are cancelled and waited for.
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
            """Wait for a free slot, then fetch one step."""
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

        :param step: the forecast hour that must be published for a run to count
        :param now: the time to search back from, for testing; defaults to the current time
        :param lookback: how far back to search before giving up
        :raises NotAvailable: no run in the lookback period has published that step
        :raises FetchError: the mirrors could not be asked

        How it works: starting at the current hour and going back an hour at a time, each
        hour at which the model runs is tested with _published, which asks the mirrors
        whether that run's step exists. The first run that has it is returned, so this
        normally costs one to three small requests.
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
        """
        Whether any mirror has published this step of this run.

        Each mirror in turn is sent a HEAD request for the model's probe URL, a small file
        that exists once the step is out. The first mirror to have it settles the matter. If
        none has it the answer is False, unless the last mirror to be asked failed instead of
        answering. That failure is raised, so that an outage is not mistaken for a run that
        has not been published.
        """
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
        """
        Fetch every requested variable for one step, trying the model's mirrors in order.

        For each mirror:

        1. The model locates the variables still outstanding. For ECMWF and NOAA this
           downloads the step's index; for ECCC it only builds URLs. A mirror that does not
           have the step is skipped. One that fails is skipped too, and the failure is
           remembered against every outstanding variable.
        2. The parts located are grouped into as few requests as possible by _plan and
           downloaded concurrently.
        3. The outcome is recorded for each variable: a Field if it arrived, the failure if
           the mirror failed, nothing if the file was not there.
        4. Variables this mirror's index did not list are given up on, since a step that
           exists without a variable lacks it on every mirror. Only what this mirror located
           but did not deliver is asked of the next one. If nothing is left, the remaining
           mirrors are not contacted.

        What happens to a variable still missing at the end depends on the last mirror that
        was asked for it. If that mirror failed, its FetchError is raised, even with
        skip_missing: a failure is never reported as data that is not published. Otherwise
        the variable is not published, which raises NotAvailable unless skip_missing is set.

        :return: the fields found, in the order the variables were requested
        """
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
        """
        Download one planned request and cut it back into its fields.

        The body is sliced at each part's offset from the start of the request. Each slice
        goes through extract, which checks that it is a complete GRIB message and, for a
        field packed into a message with others, pulls that field out. A slice that is not a
        valid message means the mirror served something other than the data, such as an error
        page or a file that does not match its index. That is raised as a FetchError, so the
        next mirror is tried.
        """
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
    """
    Group parts so that fields stored back to back, or in the same message, share a request.

    The parts are sorted by file and offset and walked in order. A part joins the previous
    request when it is in the same file and starts at or before the byte where that request
    ends. That covers fields that follow one another directly, and fields packed into one
    message, which have the same offset. The request is extended to whichever end is later.
    Any other part starts a new request, so fields with other data between them are fetched
    separately rather than downloading what lies between. A request with no end reads to the
    end of the file, and so takes in every later part of that file.
    """
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
    """
    The bytes of one part, cut from the body of the request that covered it.

    :param body_offset: where in the file the body starts
    """
    start = part.offset - body_offset
    return body[start : None if part.length is None else start + part.length]


def _model(model: Model | str) -> Model:
    """
    Turn the name of a built-in model into its Model, ignoring case.

    A Model is returned as it is. An unknown name raises ValueError listing the names there are.
    """
    if isinstance(model, Model):
        return model
    try:
        return MODELS[model.lower()]
    except KeyError:
        raise ValueError(f"unknown model {model!r}; choose from {', '.join(MODELS)}") from None


def _utc(moment: datetime) -> datetime:
    """
    The same moment as an aware UTC datetime.

    A naive datetime is taken to be in UTC already and is only labelled as such. An aware
    one is converted.
    """
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def _run_time(model: Model, run: datetime) -> datetime:
    """
    Convert a run time to UTC and check that the model runs then.

    Raises ValueError unless the time is exactly on the hour and that hour is one of the
    model's cycles, so that a mistake fails here rather than as an unexplained 404.
    """
    run = _utc(run)
    if run.hour not in model.cycles or run != run.replace(minute=0, second=0, microsecond=0):
        hours = ", ".join(f"{hour:02d}Z" for hour in model.cycles)
        raise ValueError(f"{model.name} runs at {hours}, not {run:%H:%M}Z")
    return run
