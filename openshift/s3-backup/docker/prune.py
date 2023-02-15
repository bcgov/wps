""" Simple script for pruning backups
"""
import asyncio
from datetime import datetime, timedelta
from typing import Set, List
from aiobotocore.session import get_session
from decouple import config


async def fetch_file_list(client, bucket) -> List:
    """ Fetch the list of files from Object Store. (it comes back sorted)"""
    # pylint: disable=invalid-name
    PG_HOSTNAME = config('PG_HOSTNAME')
    PG_DATABASE = config('PG_DATABASE')
    folder = f'backup/{PG_HOSTNAME}_{PG_DATABASE}'
    result = await client.list_objects_v2(Bucket=bucket, Prefix=folder)
    contents = result.get('Contents', None)
    file_list = list([])
    if contents:
        for content in contents:
            file_list.append(content.get('Key'))
    return file_list


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


class Desire:  # pylint: disable=too-few-public-methods
    """ Structure for defining and keeping track of desired backups """

    def __init__(self, desired_backups: int, interval: timedelta) -> None:
        """
        desired_backups: Number of backups desired
        interval: Desired interval (in days) between backups
        """
        self.desired_backups = desired_backups
        self.interval = interval
        self.files_to_keep = []

    def evaluate(self, new_filename) -> None:
        """ Consider the file, and manage the list of files we're deciding to keep. """
        self.files_to_keep.append(new_filename)
        self.files_to_keep.sort()
        # If we have more files than we desire:
        if len(self.files_to_keep) > self.desired_backups:
            prev_timestamp = None
            for file in self.files_to_keep:
                timestamp = extract_datetime(file)
                if prev_timestamp is None:
                    prev_timestamp = timestamp
                    continue
                # If the time difference between two files is less than the desired interval:
                if timestamp - prev_timestamp < self.interval:
                    self.files_to_keep.remove(file)
                    break
                # If the time difference between two files is greater than or equal to the interval:
                if timestamp - prev_timestamp >= self.interval:
                    prev_timestamp = timestamp
            # If we have too many files, get rid of the oldest one:
            if len(self.files_to_keep) > self.desired_backups:
                self.files_to_keep.pop(0)


def decide_files_to_keep(files: list) -> Set:
    """ Decide what files to keep
    Expects a list of filenames sorted from most recent to least recent """
    desires = [
        Desire(desired_backups=5, interval=timedelta(hours=1)),  # retain 5 hourly backups
        Desire(desired_backups=5, interval=timedelta(days=1)),  # retain 5 daily backups
        Desire(desired_backups=5, interval=timedelta(weeks=1)),  # retain 5 weekly backups
        Desire(desired_backups=5, interval=timedelta(weeks=4))]  # retain 5 monthly

    files.sort()

    for filename in files:
        for desire in desires:
            desire.evaluate(filename)

    files_to_keep = set()
    for desire in desires:
        for file in desire.files_to_keep:
            files_to_keep.add(file)

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
            files = await fetch_file_list(client, bucket)
            files_to_delete = decide_files_to_delete(files)

            # for debugging, list the files to delete
            for file in files_to_delete:
                print(file)

            if len(files_to_delete) > 0:
                await delete_files(client, bucket, files_to_delete)
        finally:
            del client


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
