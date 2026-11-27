import json

from wps_shared.db.models.auto_spatial_advisory import RunParameters
from wps_shared.utils.s3 import get_client, object_exists_v2

from app.auto_spatial_advisory.critical_hours import get_critical_hours_key


async def get_critical_hours_json_from_s3(run_params: RunParameters):
    async with get_client() as (client, bucket):
        key = get_critical_hours_key(run_params[0].for_date, run_params[0].id)
        exists = await object_exists_v2(key)
        if exists:
            res = await client.get_object(Bucket=bucket, Key=key)
            body = await res["Body"].read()
            json_content = json.loads(body)
            return json_content
        else:
            print("Critical hours json not found")
