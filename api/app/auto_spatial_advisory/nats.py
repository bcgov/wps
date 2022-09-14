""" Variables for SFMS+NATS. """
from typing import Final
import logging
from app import config

logger = logging.getLogger(__name__)

stream_prefix: Final = config.get('NATS_STREAM_PREFIX')
stream_name: Final = f'{stream_prefix}sfms'
subjects: Final = ['sfms.*', ]
