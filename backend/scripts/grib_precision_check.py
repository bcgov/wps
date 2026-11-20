# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "eccodes==2.48.0",
#     "numpy==2.3.5",
# ]
# ///
"""Report the precision each GRIB2 field is packed at, and check its integers round-trip.

A GRIB2 field is usually stored as integers X, with value = (R + X * 2**E) / 10**D, where R is
the field's reference value, E its binary scale and D its decimal scale. So the smallest step a
field can show is 2**E / 10**D, and nothing finer than that is in the file. For every field in
each file this prints R, E, D, the bits per value, that step and the range of X, and checks that
X can be recovered exactly from eccodes' decoded values: every value sits on the field's grid of
steps, to within float64 rounding, and decoding X gives the same float32 values. If so, storing X
with R, E and D is lossless against what the provider publishes. (Decoding X in float64 can
differ from eccodes in the last few bits, about 1e-14, because the arithmetic is done in another
order.)

Fields packed as IEEE floats have no integers, and are reported as such. Missing points (a
bitmap) are left out of the check.

Run it with uv on GRIB2 files already downloaded, for example by
model_grid_icechunk_spike.py, from ./backend:

    uv run scripts/grib_precision_check.py /tmp/model_grid_icechunk_spike/grib/*PT024H.grib2

Design: docs/architecture/model-grid-storage-spike.md
"""

import argparse
from pathlib import Path

import eccodes
import numpy as np


def check_field(handle) -> bool:
    """Print one field's packing. Returns whether its integers round-trip."""

    def get(key: str):
        return eccodes.codes_get(handle, key) if eccodes.codes_is_defined(handle, key) else None

    name = f"{get('shortName')} {get('typeOfLevel')} {get('level')} step {get('stepRange')}"
    packing = get("packingType")
    if packing is None or "ieee" in packing:
        print(f"  {name}: packing {packing}, floats with no integers")
        return False
    reference = get("referenceValue")
    binary_scale = get("binaryScaleFactor")
    decimal_scale = get("decimalScaleFactor")
    values = eccodes.codes_get_values(handle)
    missing = get("missingValue")
    present = values != missing if get("bitmapPresent") else np.ones(values.shape, bool)
    values = values[present]
    unrounded = (values * 10.0**decimal_scale - reference) / 2.0**binary_scale
    integers = np.rint(unrounded)
    # How far any value is from a whole X, in steps: float64 rounding only, if X is exact.
    off_grid = np.abs(unrounded - integers).max() if values.size else 0.0
    decoded = (reference + integers * 2.0**binary_scale) / 10.0**decimal_scale
    exact = off_grid < 1e-6 and np.array_equal(
        decoded.astype(np.float32), values.astype(np.float32)
    )
    print(
        f"  {name}: packing {packing}, {get('bitsPerValue')} bits, R={reference:.10g} "
        f"E={binary_scale} D={decimal_scale}, step {2.0**binary_scale / 10.0**decimal_scale:g}"
        + (f", X from {int(integers.min())} to {int(integers.max())}" if values.size else "")
        + (f", {int((~present).sum())} missing" if not present.all() else "")
        + f"\n    X recovered exactly: {exact} (furthest from a whole X: {off_grid:.2g} of a step)"
    )
    return exact


def check(path: Path) -> bool:
    """Check every field in a file. Returns whether all of them round-trip."""
    print(path.name)
    results = []
    with open(path, "rb") as grib:
        while (handle := eccodes.codes_grib_new_from_file(grib)) is not None:
            try:
                results.append(check_field(handle))
            finally:
                eccodes.codes_release(handle)
    return all(results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("files", nargs="+", type=Path, help="GRIB2 files")
    args = parser.parse_args()
    results = [check(path) for path in args.files]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
