"""Check whether our object store enforces conditional PUTs.

Delta Lake and Icechunk both rely on conditional PUTs to stop two writers overwriting each
other's commits (see docs/architecture/station-weather-storage.md). This script checks, one
request at a time, whether the store honours them:

1. If-None-Match: * on a key that does not exist     -> must succeed
2. If-None-Match: * on a key that already exists     -> must fail with 412, object unchanged
3. If-Match: <current ETag> on an existing key       -> must succeed, object replaced
4. If-Match: <stale ETag> on an existing key         -> must fail with 412, object unchanged

Delta Lake needs 1 and 2 ("create only if absent"). Icechunk needs all four. The exit code is 0
when 1 and 2 pass, since that is what the station weather design depends on.

By default there is no race: every request is sent after the previous one has finished, and each
check reads the object back to see what the store really did. That makes the result repeatable.
It shows the store honours the precondition, but not that it stays correct when two requests
arrive at the same instant.

--race-rounds adds that test. It is opt-in because it is a race by design:

5. Many writers PUT the same new key at once with If-None-Match: *. Exactly one may succeed, and
   the object must hold that writer's body. Repeated for the number of rounds given.
6. Many writers increment one counter object at once, each reading it and writing back with
   If-Match on the ETag it read, retrying when refused. No increment may be lost.

One round with two winners, or one lost increment, proves the store is not atomic. Passing proves
nothing with certainty; it is evidence, and more rounds are more evidence. All writers here share
one process and one endpoint, so writers on separate machines are a stronger test still.

It uses the backend's own S3 settings and pinned aiobotocore, so it needs no configuration beyond
what the backend already has: OBJECT_STORE_SERVER, OBJECT_STORE_USER_ID, OBJECT_STORE_SECRET and
OBJECT_STORE_BUCKET, read through wps_shared.config.

Run from ./backend with:

    uv run python scripts/object_store_conditional_put_check.py
    uv run python scripts/object_store_conditional_put_check.py --race-rounds 200

It writes a few tiny objects under a unique prefix (conditional_put_check/<random id>/ by default)
and deletes them afterwards. With --race-rounds it writes one more object per round. It touches
nothing else in the bucket.
"""

import argparse
import asyncio
import contextvars
import sys
import uuid

from aiobotocore.session import get_session
from botocore.config import Config
from botocore.exceptions import ClientError
from wps_shared import config

PASSED = "ok"
IGNORED = "IGNORED"
REJECTED = "rejected"
BROKEN = "BROKEN"


REFUSED = (409, 412)  # precondition failed, or lost a conflict with a concurrent write


class ConditionalHeaders:
    """Adds conditional headers to PutObject calls.

    The headers are injected through botocore's event system rather than passed as PutObject
    parameters, because the pinned botocore predates the IfMatch parameter. The hook runs before
    the request is signed.

    The headers for a call live in a context variable, so concurrent tasks each carry their own.
    """

    def __init__(self, client):
        self.headers = contextvars.ContextVar("conditional_headers", default=None)
        client.meta.events.register("before-call.s3.PutObject", self._add)

    def _add(self, params, **_):
        params["headers"].update(self.headers.get() or {})


async def put(client, cond, bucket, key, body, headers=None):
    """PUT an object. Returns (http status, error code or None)."""
    token = cond.headers.set(headers or {})
    try:
        response = await client.put_object(Bucket=bucket, Key=key, Body=body)
        return response["ResponseMetadata"]["HTTPStatusCode"], None
    except ClientError as error:
        return error.response["ResponseMetadata"]["HTTPStatusCode"], error.response["Error"].get(
            "Code"
        )
    finally:
        cond.headers.reset(token)


async def read(client, bucket, key):
    """Return (body, etag) of an object."""
    response = await client.get_object(Bucket=bucket, Key=key)
    async with response["Body"] as stream:
        return await stream.read(), response["ETag"]


def describe(status, code):
    return f"HTTP {status}" + (f" ({code})" if code else "")


async def check_must_succeed(name, status, code, body_now, expected_body):
    """A conditional PUT whose precondition holds. The store must accept it and store the body."""
    if status == 200 and body_now == expected_body:
        return PASSED, f"{name}: accepted, {describe(status, code)}"
    if status == 200:
        return BROKEN, f"{name}: returned 200 but the object does not hold the new body"
    return REJECTED, f"{name}: the store refused a valid conditional PUT, {describe(status, code)}"


async def check_must_fail(name, status, code, body_now, original_body):
    """A conditional PUT whose precondition does not hold. The store must refuse it."""
    unchanged = body_now == original_body
    if status in (409, 412) and unchanged:
        return PASSED, f"{name}: refused, {describe(status, code)}, object unchanged"
    if status == 200 and not unchanged:
        return IGNORED, f"{name}: the store ignored the header and overwrote the object, HTTP 200"
    if status == 200:
        return BROKEN, f"{name}: returned 200 but left the object unchanged"
    if not unchanged:
        return BROKEN, f"{name}: returned {describe(status, code)} but the object changed"
    return REJECTED, f"{name}: the store does not support the header, {describe(status, code)}"


async def run(client, bucket, prefix):
    cond = ConditionalHeaders(client)
    results = []
    created = []

    # --- If-None-Match: * (create only if absent)
    key = f"{prefix}/if-none-match"
    created.append(key)
    status, code = await put(client, cond, bucket, key, b"first", {"If-None-Match": "*"})
    body, _ = await read(client, bucket, key) if status == 200 else (None, None)
    results.append(
        await check_must_succeed("1. If-None-Match: * on a new key", status, code, body, b"first")
    )

    if status != 200:
        # The key was not created, so create it plainly to be able to run check 2.
        await put(client, cond, bucket, key, b"first")
    status, code = await put(client, cond, bucket, key, b"second", {"If-None-Match": "*"})
    body, _ = await read(client, bucket, key)
    results.append(
        await check_must_fail(
            "2. If-None-Match: * on an existing key", status, code, body, b"first"
        )
    )

    # --- If-Match: <etag> (replace only if unchanged)
    key = f"{prefix}/if-match"
    created.append(key)
    await put(client, cond, bucket, key, b"first")
    _, first_etag = await read(client, bucket, key)

    status, code = await put(client, cond, bucket, key, b"second", {"If-Match": first_etag})
    body, _ = await read(client, bucket, key)
    results.append(
        await check_must_succeed("3. If-Match with the current ETag", status, code, body, b"second")
    )

    # first_etag is now stale if check 3 replaced the object. If it did not, make it stale.
    if body != b"second":
        await put(client, cond, bucket, key, b"second")
    status, code = await put(client, cond, bucket, key, b"third", {"If-Match": first_etag})
    body, _ = await read(client, bucket, key)
    results.append(
        await check_must_fail("4. If-Match with a stale ETag", status, code, body, b"second")
    )

    return results, created


async def race_create(client, cond, bucket, prefix, rounds, writers, created):
    """Many writers create the same key at once. Exactly one may win each round."""
    violations, inconclusive = [], 0
    for i in range(rounds):
        key = f"{prefix}/race-create-{i}"
        created.append(key)
        bodies = [f"writer-{w}".encode() for w in range(writers)]
        outcomes = await asyncio.gather(
            *(put(client, cond, bucket, key, body, {"If-None-Match": "*"}) for body in bodies)
        )
        statuses = [status for status, _ in outcomes]
        winners = [w for w, status in enumerate(statuses) if status == 200]
        errors = [status for status in statuses if status != 200 and status not in REFUSED]
        if len(winners) > 1:
            violations.append(
                f"round {i}: {len(winners)} writers were all told they created the key"
            )
        elif len(winners) == 1:
            stored, _ = await read(client, bucket, key)
            if stored != bodies[winners[0]]:
                violations.append(f"round {i}: the object does not hold the winning writer's body")
        elif errors:
            inconclusive += 1  # nobody won, but some requests failed for other reasons
        else:
            violations.append(f"round {i}: every writer was refused although the key did not exist")
    return violations, inconclusive


async def race_counter(client, cond, bucket, prefix, writers, increments, created):
    """Many writers increment one counter with If-Match. No increment may be lost."""
    key = f"{prefix}/race-counter"
    created.append(key)
    await put(client, cond, bucket, key, b"0")
    gave_up = 0

    async def worker():
        nonlocal gave_up
        for _ in range(increments):
            for _attempt in range(1000):
                body, etag = await read(client, bucket, key)
                status, _ = await put(
                    client, cond, bucket, key, str(int(body) + 1).encode(), {"If-Match": etag}
                )
                if status == 200:
                    break
            else:
                gave_up += 1

    await asyncio.gather(*(worker() for _ in range(writers)))
    body, _ = await read(client, bucket, key)
    return int(body), writers * increments - gave_up, gave_up


def verdict(results):
    outcomes = [outcome for outcome, _ in results]
    create_ok = outcomes[0] == PASSED and outcomes[1] == PASSED
    update_ok = outcomes[2] == PASSED and outcomes[3] == PASSED
    lines = []
    if create_ok:
        lines.append(
            "Delta Lake: the store honours create-only-if-absent, which is what its conditional PUT mode needs."
        )
    else:
        lines.append(
            "Delta Lake: the store does NOT honour create-only-if-absent. "
            "Shared tables with several writers are not safe; use one table per writer."
        )
    if create_ok and update_ok:
        lines.append("Icechunk: the store honours both conditional create and conditional update.")
    else:
        lines.append(
            "Icechunk: the store does NOT honour both conditional create and conditional update. "
            "Only a single writer is safe."
        )
    if create_ok:
        lines.append(
            "This shows the precondition is honoured one request at a time. "
            "It does not prove atomicity when two requests arrive at the same instant."
        )
    return lines, create_ok


async def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--prefix",
        default=f"conditional_put_check/{uuid.uuid4().hex}",
        help="key prefix to write under; must be unused",
    )
    parser.add_argument(
        "--keep", action="store_true", help="do not delete the test objects afterwards"
    )
    parser.add_argument(
        "--race-rounds",
        type=int,
        default=0,
        help="also test concurrent writers, for this many rounds (default 0: no race)",
    )
    parser.add_argument("--writers", type=int, default=16, help="concurrent writers per round")
    parser.add_argument(
        "--increments", type=int, default=20, help="counter increments per writer in the race test"
    )
    args = parser.parse_args()

    names = (
        "OBJECT_STORE_SERVER",
        "OBJECT_STORE_USER_ID",
        "OBJECT_STORE_SECRET",
        "OBJECT_STORE_BUCKET",
    )
    settings = {name: config.get(name) for name in names}
    missing = [name for name, value in settings.items() if not value]
    if missing:
        sys.exit(f"Missing configuration: {', '.join(missing)}")
    bucket = settings["OBJECT_STORE_BUCKET"]
    prefix = args.prefix.strip("/")

    async with get_session().create_client(
        "s3",
        endpoint_url=f"https://{settings['OBJECT_STORE_SERVER']}",
        aws_access_key_id=settings["OBJECT_STORE_USER_ID"],
        aws_secret_access_key=settings["OBJECT_STORE_SECRET"],
        config=Config(max_pool_connections=max(10, args.writers)),
    ) as client:
        existing = await client.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/", MaxKeys=1)
        if existing.get("KeyCount", 0) > 0:
            sys.exit(f"Prefix {prefix}/ already has objects; choose an unused --prefix")

        print(f"Bucket {bucket}, prefix {prefix}/\n")
        created = [f"{prefix}/if-none-match", f"{prefix}/if-match"]
        race = None
        try:
            results, created = await run(client, bucket, prefix)
            lines, delta_ok = verdict(results)
            if args.race_rounds > 0 and delta_ok:
                cond = ConditionalHeaders(client)
                race = {
                    "create": await race_create(
                        client, cond, bucket, prefix, args.race_rounds, args.writers, created
                    )
                }
                if results[2][0] == PASSED and results[3][0] == PASSED:
                    race["counter"] = await race_counter(
                        client, cond, bucket, prefix, args.writers, args.increments, created
                    )
        finally:
            if not args.keep:
                for key in created:
                    await client.delete_object(Bucket=bucket, Key=key)

    for outcome, message in results:
        print(f"[{outcome:8s}] {message}")
    print()
    for line in lines:
        print(line)
    if args.race_rounds > 0 and not delta_ok:
        print("\nRace test skipped: the store failed the one-at-a-time checks.")
    race_ok = True
    if race:
        race_ok = report_race(race, args)
    sys.exit(0 if delta_ok and race_ok else 1)


def report_race(race, args):
    print(f"\nRace test: {args.writers} concurrent writers")
    ok = True
    violations, inconclusive = race["create"]
    if violations:
        ok = False
        print(
            f"[BROKEN  ] 5. Concurrent create: {len(violations)} of {args.race_rounds} rounds broke atomicity"
        )
        for line in violations[:10]:
            print(f"             {line}")
    else:
        print(
            f"[ok      ] 5. Concurrent create: exactly one winner in each of {args.race_rounds - inconclusive} rounds"
        )
    if inconclusive:
        print(
            f"             {inconclusive} rounds were inconclusive: no winner, and some requests failed"
        )
    if "counter" in race:
        final, expected, gave_up = race["counter"]
        if final == expected:
            print(f"[ok      ] 6. Concurrent counter: {final} increments written, none lost")
        else:
            ok = False
            print(
                f"[BROKEN  ] 6. Concurrent counter: {expected} increments succeeded but the counter reads {final}"
            )
        if gave_up:
            print(
                f"             {gave_up} increments gave up after 1000 attempts and are not counted"
            )
    else:
        print("[skipped ] 6. Concurrent counter: the store does not honour If-Match")
    print()
    if ok:
        print(
            "No atomicity violation seen. This is evidence, not proof; more rounds are more evidence."
        )
    else:
        print(
            "The store is NOT atomic under concurrent conditional PUTs. Several writers per table are not safe."
        )
    return ok


if __name__ == "__main__":
    asyncio.run(main())
