from typing import Optional, Protocol


class CacheProtocol(Protocol):
    """
    Interface for cache implementation in wps-wf1 package to support dependency injection
    """

    def get(self, key: str) -> Optional[bytes]: ...

    def set(self, key: str, value: bytes, ex: int) -> None: ...
