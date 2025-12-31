
"""Thin WFWX API client with optional caching.
"""
from wps_wf1.wfwx_settings import WfwxSettings
from wps_wf1.wfwx_client import WfwxClient
from wps_wf1.cache_protocol import CacheProtocol

__all__ = [
    'WfwxSettings',
    'WfwxClient',
    'CacheProtocol',
]
