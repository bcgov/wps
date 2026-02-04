import os


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
    Extract YYYYMMDD and run hour (HH) from MSC grib2 filenames.
    This work for RDPS, GDPS, and HRDPS from the MSC.

    """
    name = filename.rsplit(".", 1)[0]
    first_token = name.split("_", 1)[0]

    # Expected: YYYYMMDDTHHZ
    if (
        len(first_token) == 12
        and first_token[8] == "T"
        and first_token.endswith("Z")
        and first_token[:8].isdigit()
        and first_token[9:11].isdigit()
    ):
        return first_token[:8], first_token[9:11]

    raise ValueError(f"Unexpected filename format: {filename}")


def parse_eccc_forecast_hour(filename: str) -> int:
    """
    Extract forecast hour (as an integer) from MSC grib2 filenames.

    Example:
        PT039H -> 39
    """
    name = filename.rsplit(".", 1)[0]
    parts = name.split("_")

    for part in parts:
        # Expected format: PT###H
        if part.startswith("PT") and part.endswith("H") and len(part) == 6 and part[2:5].isdigit():
            return int(part[2:5])

    raise ValueError(f"Could not extract forecast hour from filename: {filename}")
