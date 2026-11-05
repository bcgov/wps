class NwpError(Exception):
    """Base class for everything wps_nwp raises on purpose."""


class NotAvailable(NwpError):
    """The data is not published (yet), or the model does not produce it for that step."""


class FetchError(NwpError):
    """No mirror could serve a request: transport failure, bad HTTP status or corrupt data."""

    def __init__(self, url: str, reason: str, status: int | None = None):
        super().__init__(f"{reason}: {url}")
        self.url = url
        self.reason = reason
        self.status = status
