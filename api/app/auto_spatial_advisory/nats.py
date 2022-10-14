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


# SFMS Stream/Subjects

# Top of hierarchy, used for creating the stream
sfms_subjects: Final = ['sfms.*', ]

# Initial version of sfms file messages, published to, and subscribed from
# Publisher should publish to the same stream with a new subject
# Consumers should subscribe to the same stream with all subjects
sfms_file_subject = 'sfms.file'
