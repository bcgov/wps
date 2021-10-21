""" Simple script for pruning backups
"""
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Generator, Tuple, List, Set
from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from decouple import config

# keep n monthly backups
# keep n weekly backups
# keep n daily backups


@asynccontextmanager
async def get_client() -> Generator[Tuple[AioBaseClient, str], None, None]:
    """ Return AioBaseClient client and bucket
    """
    server = config('OBJECT_STORE_SERVER')
    user_id = config('OBJECT_STORE_USER_ID')
    secret_key = config('OBJECT_STORE_SECRET')
    bucket = config('OBJECT_STORE_BUCKET')

    session = get_session()
    async with session.create_client('s3',
                                     endpoint_url=f'https://{server}',
                                     aws_secret_access_key=secret_key,
                                     aws_access_key_id=user_id) as client:
        try:
            yield client, bucket
        finally:
            del client


async def fetch_file_list(client, bucket):
    """ Fetch the list of files (it comes back sorted)"""
    PG_HOSTNAME = config('PG_HOSTNAME')
    PG_DATABASE = config('PG_DATABASE')
    folder = f'backup/{PG_HOSTNAME}_{PG_DATABASE}'
    result = await client.list_objects_v2(Bucket=bucket, Prefix=folder)
    contents = result.get('Contents', None)
    if contents:
        for content in contents:
            yield content.get('Key')


async def delete_files(client, bucket, files: Set):
    result = await client.delete_objects(Bucket=bucket, Delete={
        'Objects': [{'Key': file} for file in files]
    })
    print(result)


def extract_datetime(filename) -> datetime:
    date_part = filename[-26:-7]
    return datetime.strptime(date_part, '%Y-%m-%d_%H-%M-%S')


class Desire:
    """ Structure for defining and keeping track of desired backups """

    def __init__(self, desired_backups: int, interval: timedelta) -> None:
        """
        desired_backups: Number of backups desired
        interval: Desired interval (in days) between backups
        """
        self.desired_backups = desired_backups
        self.backups_found = 0
        self.prev_timestamp = None
        self.interval = interval

    def _evaluate_conditions(self, timestamp: datetime) -> bool:
        if self.backups_found < self.desired_backups:
            if self.prev_timestamp is None:
                return True
            if self.prev_timestamp - timestamp >= self.interval:
                return True
        return False

    def evaluate(self, timestamp: datetime) -> bool:
        if self._evaluate_conditions(timestamp):
            self.prev_timestamp = timestamp
            self.backups_found += 1
            return True
        return False


def decide_files_to_keep(files: list) -> List:
    """ Decide what files to keep
    Expects a list of filenames sorted from most recent to least recent """
    desires = [
        Desire(desired_backups=5, interval=timedelta(days=1)),  # retain 5 daily backups
        Desire(desired_backups=5, interval=timedelta(weeks=1)),  # retain 5 weekly backups
        Desire(desired_backups=5, interval=timedelta(weeks=4))]  # retain 5 monthly

    files_to_keep = []

    for filename in files:
        timestamp = extract_datetime(filename)
        for desire in desires:
            if desire.evaluate(timestamp):
                if filename not in files_to_keep:
                    files_to_keep.append(filename)

    return files_to_keep


def decide_files_to_delete(files: list) -> Set:
    """ Decide what files to delete """
    files_to_keep = decide_files_to_keep(files)
    file_set = set(files)
    # using set theory: files_to_delete = files - files_to_keep
    return file_set.difference(files_to_keep)


async def main():

    # Open connection to object store.
    async with get_client() as (client, bucket):
        # Get list of backup files
        files = fetch_file_list(client, bucket)
        files = list([file async for file in files])
        files.reverse()
        files_to_delete = decide_files_to_delete(files)
        if len(files_to_delete) > 0:
            await delete_files(client, bucket, files_to_delete)


if __name__ == '__main__':
    asyncio.run(main())
