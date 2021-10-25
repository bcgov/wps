""" Simple script for pruning backups
"""
import asyncio
from datetime import datetime, timedelta
from typing import Set
from aiobotocore.session import get_session
from decouple import config


async def fetch_file_list(client, bucket):
    """ Fetch the list of files from Object Store. (it comes back sorted)"""
    PG_HOSTNAME = config('PG_HOSTNAME')
    PG_DATABASE = config('PG_DATABASE')
    folder = f'backup/{PG_HOSTNAME}_{PG_DATABASE}'
    result = await client.list_objects_v2(Bucket=bucket, Prefix=folder)
    contents = result.get('Contents', None)
    if contents:
        for content in contents:
            yield content.get('Key')


async def delete_files(client, bucket, files: Set):
    """ Delete files in Object Store. """
    result = await client.delete_objects(Bucket=bucket, Delete={
        'Objects': [{'Key': file} for file in files]
    })
    print(result)


def extract_datetime(filename) -> datetime:
    """ Extract date object from filename """
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

    def _is_keeper(self, timestamp: datetime) -> bool:
        """ Run through all the conditions to decide if we keep this timestamp or not. """
        if self.backups_found < self.desired_backups:
            # If we don't have any backups yet, keep it!
            if self.prev_timestamp is None:
                return True
            # If this backup is older than the previous interval, keep it!
            if self.prev_timestamp - timestamp >= self.interval:
                return True
        return False

    def is_keeper(self, timestamp: datetime) -> bool:
        """ Decide if we should keep this timestamp or not. """
        if self._is_keeper(timestamp):
            self.prev_timestamp = timestamp
            self.backups_found += 1
            return True
        return False


def decide_files_to_keep(files: list) -> Set:
    """ Decide what files to keep
    Expects a list of filenames sorted from most recent to least recent """
    desires = [
        Desire(desired_backups=5, interval=timedelta(days=1)),  # retain 5 daily backups
        Desire(desired_backups=5, interval=timedelta(weeks=1)),  # retain 5 weekly backups
        Desire(desired_backups=5, interval=timedelta(weeks=4))]  # retain 5 monthly

    files_to_keep = set()

    for filename in files:
        timestamp = extract_datetime(filename)
        for desire in desires:
            if desire.is_keeper(timestamp):
                if filename not in files_to_keep:
                    files_to_keep.add(filename)

    return files_to_keep


def decide_files_to_delete(files: list) -> Set:
    """ Decide what files to delete """
    files_to_keep = decide_files_to_keep(files)
    file_set = set(files)
    # using set theory: files_to_delete = files - files_to_keep
    return file_set.difference(files_to_keep)


async def main():
    """ Entry point. """

    # Open connection to object store.
    server = config('AWS_HOSTNAME')
    user_id = config('AWS_ACCESS_KEY')
    secret_key = config('AWS_SECRET_KEY')
    bucket = config('AWS_BUCKET')

    session = get_session()
    async with session.create_client('s3',
                                     endpoint_url=f'https://{server}',
                                     aws_secret_access_key=secret_key,
                                     aws_access_key_id=user_id) as client:
        try:
            # Get list of backup files
            files = fetch_file_list(client, bucket)
            files = list([file async for file in files])
            files.reverse()
            files_to_delete = decide_files_to_delete(files)
            if len(files_to_delete) > 0:
                await delete_files(client, bucket, files_to_delete)
        finally:
            del client


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
