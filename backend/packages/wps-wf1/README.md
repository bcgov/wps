# wps_wf1 module

This package contains code for interacting with the Wildfire One API.

The key modules are `wfwx_api.py`, `wfwx_client.py` and `parsers.py`.

## wfwx_api.py

This is the entrypoint for consumers wanting to either request data from or POST data to the WF1 API. It contains convenience functions for requesting data and having it returned in specific shapes/models.

## wfwx_client.py

This module performs the actual work of sending requests to the WF1 API.
