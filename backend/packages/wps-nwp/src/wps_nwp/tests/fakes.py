"""Stand-ins for the network and for model output, so tests never leave the process."""

import numpy as np


class FakeSession:
    """
    Plays the part of aiohttp.ClientSession.

    routes maps a URL to what requesting it does: bytes are served (honouring Range), an int
    is returned as the HTTP status, and an exception is raised. A list gives one of those per
    request, repeating the last. URLs that are not listed return 404.
    """

    def __init__(self, routes: dict, *, honour_range: bool = True):
        self.routes = routes
        self.honour_range = honour_range
        self.requests: list[tuple[str, str, str | None]] = []  # method, url, Range header

    def request(self, method: str, url: str, headers: dict | None = None):
        byte_range = (headers or {}).get("Range")
        self.requests.append((method, url, byte_range))
        reply = self.routes.get(url, 404)
        if isinstance(reply, list):
            reply = reply.pop(0) if len(reply) > 1 else reply[0]
        return _Reply(reply, byte_range if self.honour_range else None)

    def urls(self) -> list[str]:
        return [url for _, url, _ in self.requests]


class _Reply:
    def __init__(self, reply, byte_range: str | None):
        self.headers: dict[str, str] = {}
        self._reply = reply
        self._body = b""
        self.status = 200
        if isinstance(reply, int):
            self.status = reply
        elif isinstance(reply, bytes):
            self._body = reply
            if byte_range:
                first, _, last = byte_range.removeprefix("bytes=").partition("-")
                self._body = reply[int(first) : int(last) + 1 if last else None]
                self.status = 206

    async def __aenter__(self):
        if isinstance(self._reply, Exception):
            raise self._reply
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def read(self) -> bytes:
        return self._body


def fake_grib(*fields: bytes) -> bytes:
    """
    A message with the layout of GRIB2 but nothing decodable in it.

    Each field gets its own sections 4 to 7 and shares sections 1 and 3, which is how NOAA
    packs several fields into one message.
    """

    def section(number: int, payload: bytes) -> bytes:
        return (5 + len(payload)).to_bytes(4) + bytes([number]) + payload

    body = section(1, b"identification") + section(3, b"grid")
    for payload in fields:
        body += section(4, b"product") + section(5, b"repr") + section(6, b"") + section(7, payload)
    total = 16 + len(body) + 4
    return b"GRIB\x00\x00\x00\x02" + total.to_bytes(8) + body + b"7777"


def real_grib(
    values,
    *,
    short_name: str = "2t",
    first_lat: float = 60.0,
    first_lon: float = -130.0,
    spacing: float = 1.0,
    missing: float | None = None,
    south_to_north: bool = False,
    rotated_south_pole: tuple[float, float] | None = None,
) -> bytes:
    """
    A decodable GRIB2 message on a regular lat/lon grid.

    Rows run north to south from first_lat unless south_to_north is set. With
    rotated_south_pole the grid is regular in a frame whose south pole is at that (lat, lon),
    as RDPS and HRDPS are, and first_lat and first_lon are in that frame.
    """
    import eccodes  # optional for the package, so only needed by the tests that decode

    values = np.asarray(values, dtype=float)
    rows, columns = values.shape
    lat_step = spacing if south_to_north else -spacing
    sample = "rotated_ll_sfc_grib2" if rotated_south_pole else "regular_ll_sfc_grib2"
    handle = eccodes.codes_grib_new_from_samples(sample)
    try:
        keys = {
            "Ni": columns,
            "Nj": rows,
            "jScansPositively": int(south_to_north),
            "latitudeOfFirstGridPointInDegrees": first_lat,
            "longitudeOfFirstGridPointInDegrees": first_lon % 360,
            "latitudeOfLastGridPointInDegrees": first_lat + lat_step * (rows - 1),
            "longitudeOfLastGridPointInDegrees": (first_lon + spacing * (columns - 1)) % 360,
            "iDirectionIncrementInDegrees": spacing,
            "jDirectionIncrementInDegrees": spacing,
            "shortName": short_name,
        }
        if rotated_south_pole:
            keys["latitudeOfSouthernPoleInDegrees"] = rotated_south_pole[0]
            keys["longitudeOfSouthernPoleInDegrees"] = rotated_south_pole[1] % 360
            keys["angleOfRotationInDegrees"] = 0.0
        for key, value in keys.items():
            eccodes.codes_set(handle, key, value)
        if missing is not None:
            eccodes.codes_set(handle, "bitmapPresent", 1)
            eccodes.codes_set(handle, "missingValue", missing)
        eccodes.codes_set_values(handle, values.ravel())
        return eccodes.codes_get_message(handle)
    finally:
        eccodes.codes_release(handle)
