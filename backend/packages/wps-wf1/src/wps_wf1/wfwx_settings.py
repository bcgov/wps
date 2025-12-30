from dataclasses import dataclass


@dataclass(frozen=True)
class WfwxSettings:
    base_url: str
    auth_url: str
    user: str
    secret: str
    max_page_size: int = 1000
