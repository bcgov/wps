""" Variables for SFMS+NATS. """
from typing import Final
import logging
from app import config

logger = logging.getLogger(__name__)

server: Final = config.get('NATS_SERVER')

stream_prefix: Final = config.get('NATS_STREAM_PREFIX')
stream_name: Final = f'{stream_prefix}sfms'
subjects: Final = ['sfms.*', ]

hfi_classify_group: Final = "hfi_classify"
