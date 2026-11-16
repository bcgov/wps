"""Check that Delta Lake works against our object store, including several writers at once.

This is step 1 of the plan in docs/architecture/station-weather-storage.md. The object store has
already passed object_store_conditional_put_check.py, which used our own S3 client. Delta Lake
brings a different client, so this runs the `deltalake` library itself against the store, in a
throwaway table, and answers:

1. Which storage options work?         Tries Delta's conditional PUT mode, then the library
                                       default, then the unsafe-rename mode (single writer only).
2. Is it safe with several writers?    Several processes append to one table at the same time.
                                       Every commit they were told succeeded must be in the table.
3. Do the operations we need work?     MERGE, optimize, checkpoint and vacuum.
4. How long do reads take?             A cold table open and a filtered read. The table is tiny,
                                       so this is the fixed cost per request, not a throughput test.

Step 2 is a race by design. One lost commit proves several writers are not safe. A clean run is
evidence, not proof; --appends and --writers raise the load. All writers run on this machine, so
writers in separate pods are a stronger test still.

It reads the backend's own S3 settings through wps_shared.config: OBJECT_STORE_SERVER,
OBJECT_STORE_USER_ID, OBJECT_STORE_SECRET and OBJECT_STORE_BUCKET. `deltalake` and `pyarrow` are
not backend dependencies yet, so add them for this run. From ./backend:

    uv run --with deltalake==1.6.6 --with pyarrow python scripts/object_store_delta_check.py

It writes under a unique prefix (delta_check/<random id>/ by default) and deletes everything under
that prefix afterwards. It touches nothing else in the bucket.

--local DIR runs the same steps against a local directory instead, to try the script itself.
"""

import argparse
import asyncio
import multiprocessing
import re
import shutil
import statistics
import sys
import time
import uuid
from pathlib import Path

import deltalake
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

SCHEMA = pa.schema([("writer", pa.int32()), ("seq", pa.int32()), ("value", pa.string())])

# (name, extra storage options, safe for several writers)
MODES = [
    ("conditional PUT", {"conditional_put": "etag"}, True),
    ("library default", {}, True),
    ("unsafe rename", {"AWS_S3_ALLOW_UNSAFE_RENAME": "true"}, False),
]


def rows(writer, seqs, value):
    return pa.table(
        {"writer": [writer] * len(seqs), "seq": list(seqs), "value": [value] * len(seqs)},
        schema=SCHEMA,
    )


def short(error):
    """One line of the error, without the terminal colour codes the library adds."""
    text = " ".join(re.sub(r"\x1b\[[0-9;]*m", "", str(error)).split())
    return text if len(text) <= 300 else text[:300] + "..."


def try_mode(uri, options):
    """Create a table, append to it and read it back. Returns None, or the error."""
    try:
        write_deltalake(uri, rows(0, [0], "created"), storage_options=options)
        write_deltalake(uri, rows(0, [1], "appended"), mode="append", storage_options=options)
        count = DeltaTable(uri, storage_options=options).to_pyarrow_table().num_rows
        return None if count == 2 else f"expected 2 rows, read {count}"
    except Exception as error:  # noqa: BLE001 - report whatever the library raises
        return short(error)


def append_worker(uri, options, writer, appends, start, results):
    """Append one row per commit, as fast as possible, once every writer is ready."""
    start.wait()
    succeeded, failed = [], []
    for seq in range(appends):
        try:
            write_deltalake(
                uri, rows(writer, [seq], "raced"), mode="append", storage_options=options
            )
            succeeded.append(seq)
        except Exception as error:  # noqa: BLE001
            failed.append((seq, short(error)))
    results.put((writer, succeeded, failed))


def concurrent_appends(uri, options, writers, appends):
    """Returns (ok, lines)."""
    write_deltalake(uri, rows(-1, [0], "created"), storage_options=options)
    ctx = multiprocessing.get_context("spawn")
    start, results = ctx.Event(), ctx.Queue()
    processes = [
        ctx.Process(target=append_worker, args=(uri, options, w, appends, start, results))
        for w in range(writers)
    ]
    for process in processes:
        process.start()
    time.sleep(2)  # let every process import and reach the barrier
    start.set()
    outcomes = [results.get(timeout=1800) for _ in processes]
    for process in processes:
        process.join()

    table = DeltaTable(uri, storage_options=options)
    stored = table.to_pyarrow_table().to_pylist()
    present = [(r["writer"], r["seq"]) for r in stored if r["writer"] >= 0]
    told_ok = {(w, seq) for w, succeeded, _ in outcomes for seq in succeeded}
    failures = [(w, seq, error) for w, _, failed in outcomes for seq, error in failed]

    lost = told_ok - set(present)
    duplicated = len(present) - len(set(present))
    unexpected = set(present) - told_ok
    lines = [
        (
            f"{writers} writers x {appends} appends: {len(told_ok)} commits reported as succeeded, "
            f"{len(failures)} reported as failed, table is at version {table.version()}"
        )
    ]
    if lost:
        lines.append(
            f"LOST: {len(lost)} commits were reported as succeeded but are not in the table"
        )
    if duplicated:
        lines.append(f"DUPLICATED: {duplicated} rows appear more than once")
    if unexpected:
        lines.append(
            f"{len(unexpected)} commits were reported as failed but are in the table "
            "(the writer cannot tell they landed)"
        )
    for w, seq, error in failures[:5]:
        lines.append(f"writer {w} append {seq} failed: {error}")
    return not lost and not duplicated, lines


def operations(uri, options):
    """MERGE, optimize, checkpoint and vacuum on the table from the concurrent test."""
    lines, ok = [], True

    def step(name, action):
        nonlocal ok
        try:
            lines.append(f"[ok      ] {name}: {action()}")
        except Exception as error:  # noqa: BLE001
            ok = False
            lines.append(f"[FAILED  ] {name}: {short(error)}")

    def merge():
        table = DeltaTable(uri, storage_options=options)
        before = table.to_pyarrow_table().num_rows
        source = pa.concat_tables([rows(0, [0, 1], "merged"), rows(999, [0, 1, 2], "merged")])
        (
            table.merge(
                source, "t.writer = s.writer AND t.seq = s.seq", source_alias="s", target_alias="t"
            )
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute()
        )
        after = DeltaTable(uri, storage_options=options).to_pyarrow_table()
        merged = after.filter(pa.compute.equal(after["value"], "merged")).num_rows
        if after.num_rows != before + 3 or merged != 5:
            raise RuntimeError(
                f"expected {before + 3} rows with 5 merged, got {after.num_rows} and {merged}"
            )
        return "2 rows updated, 3 inserted"

    def optimize():
        table = DeltaTable(uri, storage_options=options)
        before = len(table.file_uris())
        table.optimize.compact()
        after = len(DeltaTable(uri, storage_options=options).file_uris())
        return f"{before} files compacted to {after}"

    def checkpoint():
        DeltaTable(uri, storage_options=options).create_checkpoint()
        return "written"

    def vacuum():
        table = DeltaTable(uri, storage_options=options)
        before = table.to_pyarrow_table().num_rows
        removed = table.vacuum(retention_hours=0, dry_run=False, enforce_retention_duration=False)
        after = DeltaTable(uri, storage_options=options).to_pyarrow_table().num_rows
        if after != before:
            raise RuntimeError(f"row count changed from {before} to {after}")
        return f"{len(removed)} unreferenced files deleted, row count unchanged"

    step("MERGE", merge)
    step("optimize", optimize)
    step("checkpoint", checkpoint)
    step("vacuum", vacuum)
    return ok, lines


def timings(uri, options):
    opens, reads = [], []
    for _ in range(5):
        t = time.perf_counter()
        table = DeltaTable(uri, storage_options=options)
        opens.append(time.perf_counter() - t)
        t = time.perf_counter()
        table.to_pyarrow_dataset().to_table(filter=pa.dataset.field("writer") == 0)
        reads.append(time.perf_counter() - t)
    return statistics.median(opens) * 1000, statistics.median(reads) * 1000


async def delete_prefix(settings, prefix):
    """Delete every object under the prefix, one request each."""
    from aiobotocore.session import get_session

    deleted = 0
    async with get_session().create_client(
        "s3",
        endpoint_url=f"https://{settings['OBJECT_STORE_SERVER']}",
        aws_access_key_id=settings["OBJECT_STORE_USER_ID"],
        aws_secret_access_key=settings["OBJECT_STORE_SECRET"],
    ) as client:
        bucket = settings["OBJECT_STORE_BUCKET"]
        while True:
            page = await client.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/")
            keys = [item["Key"] for item in page.get("Contents", [])]
            if not keys:
                return deleted
            for key in keys:
                await client.delete_object(Bucket=bucket, Key=key)
            deleted += len(keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--prefix", default=f"delta_check/{uuid.uuid4().hex}", help="key prefix to write under"
    )
    parser.add_argument("--writers", type=int, default=4, help="concurrent writer processes")
    parser.add_argument("--appends", type=int, default=10, help="appends per writer")
    parser.add_argument(
        "--keep", action="store_true", help="do not delete the test tables afterwards"
    )
    parser.add_argument(
        "--local", type=Path, help="use this local directory instead of the object store"
    )
    args = parser.parse_args()
    prefix = args.prefix.strip("/")

    if args.local:
        settings = None
        root = str(args.local.resolve() / prefix)
        base_options = {}
        modes = [("local filesystem", {}, True)]
        print(f"Local directory {root}")
    else:
        from wps_shared import config

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
        root = f"s3://{settings['OBJECT_STORE_BUCKET']}/{prefix}"
        base_options = {
            "AWS_ENDPOINT_URL": f"https://{settings['OBJECT_STORE_SERVER']}",
            "AWS_ACCESS_KEY_ID": settings["OBJECT_STORE_USER_ID"],
            "AWS_SECRET_ACCESS_KEY": settings["OBJECT_STORE_SECRET"],
            "AWS_REGION": "us-east-1",
        }
        modes = MODES
        print(f"Bucket {settings['OBJECT_STORE_BUCKET']}, prefix {prefix}/")
    print(f"deltalake {deltalake.__version__}, pyarrow {pa.__version__}\n")

    ok = False
    try:
        print("1. Which storage options work?")
        working = []
        for i, (name, extra, safe) in enumerate(modes):
            error = try_mode(f"{root}/mode-{i}", {**base_options, **extra})
            note = "" if safe else " (single writer only)"
            if error is None:
                working.append((name, extra, safe))
                print(f"[ok      ] {name}{note}: {extra or 'no extra options'}")
            else:
                print(f"[FAILED  ] {name}{note}: {error}")

        chosen = next((mode for mode in working if mode[2]), None)
        if chosen is None:
            print("\nNo mode that is safe for several writers works against this store.")
            if working:
                print("Only the unsafe-rename mode works: use one table per writer.")
            return 1
        name, extra, _ = chosen
        options = {**base_options, **extra}
        uri = f"{root}/table"
        print(f"\nUsing '{name}' for the remaining steps.")

        print("\n2. Is it safe with several writers?")
        writers_ok, lines = concurrent_appends(uri, options, args.writers, args.appends)
        print(f"[{'ok      ' if writers_ok else 'BROKEN  '}] " + "\n           ".join(lines))

        print("\n3. Do the operations we need work?")
        operations_ok, lines = operations(uri, options)
        print("\n".join(lines))

        print("\n4. How long do reads take?")
        open_ms, read_ms = timings(uri, options)
        print(
            f"           cold open {open_ms:.0f} ms, filtered read {read_ms:.0f} ms (median of 5, tiny table)"
        )

        ok = writers_ok and operations_ok
        print()
        if writers_ok:
            print(
                "No commit was lost. This is evidence that several writers per table are safe, not proof."
            )
            if extra:
                print(f"Storage options to use, besides the endpoint and credentials: {extra}")
        else:
            print(
                "Commits were lost. Several writers per table are NOT safe: use one table per writer."
            )
        if not operations_ok:
            print("One or more Delta operations failed; see step 3.")
    finally:
        if not args.keep:
            if args.local:
                shutil.rmtree(root, ignore_errors=True)
            else:
                deleted = asyncio.run(delete_prefix(settings, prefix))
                print(f"\nDeleted {deleted} objects under {prefix}/")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
