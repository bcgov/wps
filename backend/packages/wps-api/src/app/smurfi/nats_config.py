from typing import Final

from wps_shared import config

server: Final = config.get("NATS_SERVER")
stream_prefix: Final = config.get("NATS_STREAM_PREFIX")
stream_name: Final = f"{stream_prefix}smurfi"
subjects: Final = ["smurfi.>"]
smurfi_spot_update_subject: Final = "smurfi.spot.update"
smurfi_spot_update_durable: Final = "smurfi_spot_update"
