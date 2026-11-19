# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "eccodes==2.48.0",
#     "numpy==2.3.5",
# ]
# ///
"""Report the precision MSC packs each GRIB2 field at, and check its integers round-trip.

A GRIB2 field is stored as integers X, with value = (R + X * 2**E) / 10**D, where R is the
field's reference value, E its binary scale and D its decimal scale. So the smallest step a
field can show is 2**E / 10**D, and nothing finer than that is in the file. For each file this
prints R, E, D, the bits per value, that step and the range of X, and checks that X can be
recovered exactly from eccodes' decoded values: every value sits on the field's grid of steps,
to within float64 rounding, and decoding X gives the same float32 values. If so, storing X with
R, E and D is lossless against what MSC publishes. (Decoding X in float64 can differ from
eccodes in the last few bits, about 1e-14, because the arithmetic is done in another order.)

Run it with uv on GRIB2 files already downloaded, for example by
model_grid_icechunk_spike.py, from ./backend:

    uv run scripts/msc_grib_precision_check.py /tmp/model_grid_icechunk_spike/grib/*PT024H.grib2

Design: docs/architecture/model-grid-storage-spike.md
"""

import argparse
from pathlib import Path

import eccodes
import numpy as np


def check(path: Path) -> bool:
    """Print the file's first field's packing. Returns whether its integers round-trip."""
    with open(path, "rb") as grib:
        handle = eccodes.codes_grib_new_from_file(grib)
        try:
            reference = eccodes.codes_get(handle, "referenceValue")
            binary_scale = eccodes.codes_get(handle, "binaryScaleFactor")
            decimal_scale = eccodes.codes_get(handle, "decimalScaleFactor")
            bits = eccodes.codes_get(handle, "bitsPerValue")
            packing = eccodes.codes_get(handle, "packingType")
            values = eccodes.codes_get_values(handle)
        finally:
            eccodes.codes_release(handle)
    unrounded = (values * 10.0**decimal_scale - reference) / 2.0**binary_scale
    integers = np.rint(unrounded)
    # How far any value is from a whole X, in steps: float64 rounding only, if X is exact.
    off_grid = np.abs(unrounded - integers).max()
    decoded = (reference + integers * 2.0**binary_scale) / 10.0**decimal_scale
    exact = off_grid < 1e-6 and np.array_equal(
        decoded.astype(np.float32), values.astype(np.float32)
    )
    print(
        f"{path.name}\n"
        f"  packing {packing}, {bits} bits, R={reference:.10g} E={binary_scale} D={decimal_scale}"
        f", step {2.0**binary_scale / 10.0**decimal_scale:g}"
        f", X from {int(integers.min())} to {int(integers.max())}\n"
        f"  X recovered exactly: {exact} (furthest from a whole X: {off_grid:.2g} of a step;"
        f" float64 decode differs by up to {np.abs(decoded - values).max():.2g})"
    )
    return exact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("files", nargs="+", type=Path, help="GRIB2 files")
    args = parser.parse_args()
    results = [check(path) for path in args.files]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
