#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "logging",
#     "requests>=2.32.5",
# ]
# ///

# --------------------------------------------------------------------------------------------------
# Author: Laurence Perry
# Ministry, Division, Branch: EMLI, MCAD, Regional Operations
# Updated: 2024-04-16
# Description:
#    A function to pull responses in JSON form from the Common Hosted Forms (CHEFS) API.
#    Note that a form ID and API token are required to access the API, this is demonstrated in the
#    read me in more detail.
# Modified: 2024-09-06 by Brian Mang
# --------------------------------------------------------------------------------------------------
import requests
import base64
import logging
import json
import os
from wps_shared import config

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
)


# Load configuration from config.json or environment variables
def _load_config():
    """Load configuration from config.json with env var overrides"""
    chefs_config_file = os.path.join(os.path.dirname(__file__), "config.json")
    chefs_config = {}

    if os.path.exists(chefs_config_file):
        try:
            with open(chefs_config_file, "r") as f:
                chefs_config = json.load(f)
        except Exception as e:
            logging.warning(f"Could not read config.json: {e}")

    # Environment variables override config file
    chefs_config["form_id"] = config.get("CHEFS_FORM_ID") or chefs_config.get("form_id")
    chefs_config["api_token"] = config.get("CHEFS_API_TOKEN") or chefs_config.get("api_token")
    chefs_config["version"] = chefs_config.get("version", "0")
    chefs_config["base_url"] = chefs_config.get("base_url", "https://submit.digital.gov.bc.ca/")
    chefs_config["file_component"] = chefs_config.get("file_component", ["simplefile"])
    chefs_config["api_params"] = chefs_config.get("api_params", {})

    return chefs_config


chefs_config = _load_config()


def write_request_if_missing(files_dir: str, submission_id: str, payload: dict):
    filename = f"spot_request_{submission_id}.json"
    file_path = os.path.join(files_dir, filename)

    if os.path.exists(file_path):
        logging.info(f"File already exists, skipping: {filename}")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logging.info(f"Created file: {filename}")


def get_chefs_submissions_json():
    """
    Returns the processed spot weather requests from the CHEFS API.

    Returns:
        list: List of processed spot weather request dictionaries.

    Raises:
        ValueError: If required credentials are missing.
    """
    chefs_config = _load_config()
    form_id = chefs_config.get("form_id")
    api_token = chefs_config.get("api_token")
    version = chefs_config.get("version", "0")

    # Validate required credentials
    if not form_id or not api_token:
        raise ValueError(
            "Missing required credentials: CHEFS_FORM_ID and CHEFS_API_TOKEN must be set"
        )

    # Ensure a local directory exists for downloaded files
    files_dir = os.path.join(os.path.dirname(__file__), "files")
    os.makedirs(files_dir, exist_ok=True)

    username_password = f"{form_id}:{api_token}"
    base64_encoded_credentials = base64.b64encode(username_password.encode("utf-8")).decode("utf-8")

    headers = {"Authorization": f"Basic {base64_encoded_credentials}"}
    base_url = chefs_config.get("base_url", "https://submit.digital.gov.bc.ca")
    # Remove trailing slash if present
    base_url = base_url.rstrip("/")

    url = f"{base_url}/app/api/v1/forms/{form_id}/export"
    params = {"format": "json", "type": "submissions", "version": version}

    # Merge with optional API parameters
    api_params = chefs_config.get("api_params", {})
    if isinstance(api_params, dict):
        params.update(api_params)

    logging.info(f"Export URL: {url}")
    logging.info(f"Params: {params}")
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        logging.error(f"Export request failed: {response.status_code} {response.text}")
        return []

    processed_requests = []
    try:
        data = response.json()

        for chefs_request in data:
            form_meta = chefs_request.get("form", {})
            submission_id = form_meta.get("submissionId")

            if not submission_id:
                logging.warning("Skipping submission with no submissionId")
                continue

            spot_wx_request = {
                "metadata": form_meta,
                "fire_number": chefs_request["fireNumber"],
                "forecast_end_date": chefs_request["forecastEndDate"],
                "forecast_start_date": chefs_request["forecastStartDate"],
                "spot_forecast_type": chefs_request["spotForecastType"],
                "email_distribution_list": chefs_request["emailDistributionListForSpotForecast"],
                "additional_info": chefs_request["additionalInformation"] or None,
                "latitude": chefs_request["LatLong"]["features"][0]["coordinates"]["lat"],
                "longitude": chefs_request["LatLong"]["features"][0]["coordinates"]["lng"],
            }
            # write_request_if_missing(files_dir, submission_id, spot_wx_request)
            processed_requests.append(spot_wx_request)
    except Exception as e:
        logging.error(f"Failed to parse JSON response: {e}")
        return []

    if not isinstance(data, list):
        logging.warning(
            f"Unexpected response shape (not a list). Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )
        return []

    logging.info(f"Submissions returned: {len(data)}")
    logging.info(f"Processed requests: {len(processed_requests)}")

    return processed_requests


if __name__ == "__main__":
    try:
        response = get_chefs_submissions_json(
            chefs_config["form_id"], chefs_config["api_token"], chefs_config["version"]
        )
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)
