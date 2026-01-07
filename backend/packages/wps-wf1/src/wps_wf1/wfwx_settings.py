from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WfwxSettings:
    base_url: str
    auth_url: str
    user: str
    secret: str
    max_page_size: Optional[int] = 1000
    auth_cache_expiry: Optional[int] = 600
    station_cache_expiry: Optional[int] = 604800
    hourlies_by_station_code_expiry: Optional[int] = 300
    dailies_by_station_code_expiry: Optional[int] = 300
    use_cache: Optional[bool] = True  # flag to optionally disable caching
