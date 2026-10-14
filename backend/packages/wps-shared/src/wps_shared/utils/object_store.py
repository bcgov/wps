import ipaddress
from urllib.parse import urlparse

from wps_shared.config import get as get_config


def normalize_endpoint_url(endpoint_url: str) -> str:
    """Validate and normalize an S3-compatible endpoint URL."""
    parsed = urlparse(endpoint_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Object-store endpoint must be a complete http:// or https:// URL")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("Object-store endpoint must not include a path, query, or fragment")
    return endpoint_url.rstrip("/")


def get_endpoint_url(server: str | None = None) -> str:
    """use the configured URL or default a hostname to HTTPS."""
    resolved_server = server or get_config("OBJECT_STORE_SERVER")
    if not resolved_server:
        raise ValueError("OBJECT_STORE_SERVER must be configured")
    if "://" in resolved_server:
        return normalize_endpoint_url(resolved_server)
    return f"https://{resolved_server}"


def get_gdal_endpoint() -> tuple[str, bool]:
    """Return the host-style GDAL endpoint and whether it uses HTTPS."""
    parsed = urlparse(get_endpoint_url())
    return parsed.netloc, parsed.scheme == "https"


def is_loopback_endpoint(endpoint_url: str) -> bool:
    """Return whether an endpoint is restricted to the local machine."""
    hostname = urlparse(normalize_endpoint_url(endpoint_url)).hostname
    if hostname == "localhost":
        return True
    if not hostname:
        return False
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False
