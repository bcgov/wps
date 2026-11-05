class NwpError(Exception):
    """Base class for everything wps_nwp raises on purpose."""


class NotAvailable(NwpError):
    """The data is not published (yet), or the model does not produce it for that step."""


class FetchError(NwpError):
    """No mirror could serve a request: transport failure, bad HTTP status or corrupt data."""

    def __init__(self, url: str, reason: str, status: int | None = None):
        """
        :param url: the request that failed
        :param reason: what went wrong, such as "HTTP 503" or the name of a transport error
        :param status: the HTTP status if the server answered with an error, otherwise None
            (no response at all, or a response whose body was short or not valid GRIB)
        """
        super().__init__(f"{reason}: {url}")
        self.url = url
        self.reason = reason
        self.status = status
