import os
import re


def s3_key_from_eccc_path(s3_prefix: str, path: str) -> str:
    """
    Return the portion of a path that comes *after* 'WXO-DD/'.


    :param path: Env Canada grib url
    :raises ValueError: _description_
    :return: s3_key for ECCC grib file.
    """
    marker = "/WXO-DD/"

    # partition() splits the string into:
    #   (before_marker, marker_itself, after_marker)
    before, found_marker, after = path.partition(marker)

    if not found_marker:
        raise ValueError(f"Expected '{marker}' in path: {path}")

    date = before.split("/")[-1]

    # ex. {prefix}/20260203/model_rdps/10km/18/058/20260203T18Z_MSC_RDPS_RelativeHumidity_IsbL-0500_RLatLon0.09_PT058H.grib2
    return os.path.join(s3_prefix, date, after)


def parse_date_and_run(filename: str) -> tuple[str, str]:
    """
    Extract YYYYMMDD and run hour (HH) from MSC/CMC grib2 filenames.

    Handles two formats:
    - MSC format: YYYYMMDDTHHZ_MSC_... (RDPS, GDPS, HRDPS)
    - CMC format: CMC_glb_..._YYYYMMDDHH_P... (GEM global)
    """
    name = filename.rsplit(".", 1)[0]
    first_token = name.split("_", 1)[0]

    # MSC format: filename starts with YYYYMMDDTHHZ
    if (
        len(first_token) == 12
        and first_token[8] == "T"
        and first_token.endswith("Z")
        and first_token[:8].isdigit()
        and first_token[9:11].isdigit()
    ):
        return first_token[:8], first_token[9:11]

    # CMC format: date/run appears mid-filename as _YYYYMMDDHH_
    match = re.search(r"_(\d{8})(\d{2})_", filename)
    if match:
        return match.group(1), match.group(2)

    raise ValueError(f"Unexpected filename format: {filename}")
