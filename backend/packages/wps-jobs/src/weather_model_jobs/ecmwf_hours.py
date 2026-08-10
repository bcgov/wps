from collections.abc import Iterator


def get_ecmwf_forecast_hours() -> Iterator[int]:
    yield from range(0, 145, 3)
    yield from range(150, 241, 6)
