""" Tests for prune.py
"""
from datetime import datetime, timedelta
import unittest
from prune import decide_files_to_keep, decide_files_to_delete


class TestPrune(unittest.TestCase):
    """ Unit tests for prune.py """

    """
    file list:
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-15_09-00-05.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-15_14-00-05.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-15_20-00-05.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-16_03-00-05.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-16_09-00-03.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-16_14-00-17.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-16_20-00-13.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-17_03-00-09.sql.gz
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-17_09-00-06.sql.gz
files to delete:
backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-16_03-00-05.sql.gz
{'ResponseMetadata': {'RequestId': '8e22ee0c:17bb6669ed6:8900c:3980', 'HostId': '6718bcb60b5b455c64b56e338a0d9199753e4be2ea200341ed18c18bde808b71', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Wed, 17 Nov 2021 09:01:24 GMT', 'server': 'ViPR/1.0', 'x-amz-request-id': '8e22ee0c:17bb6669ed6:8900c:3980', 'x-amz-id-2': '6718bcb60b5b455c64b56e338a0d9199753e4be2ea200341ed18c18bde808b71', 'content-type': 'application/xml', 'content-length': '394'}, 'RetryAttempts': 0}, 'Deleted': [{'Key': 'backup/patroni-wps-pr-1525-leader_wps/2021/11/patroni-wps-pr-1525-leader_wps_2021-11-16_03-00-05.sql.gz', 'VersionId': '1637139684765', 'DeleteMarker': True, 'DeleteMarkerVersionId': '1637139684765'}]}



2021-11-15_09
h 2021-11-15_14
d h 2021-11-15_20

2021-11-16_03
2021-11-16_09


2021-11-16_14
2021-11-16_20
2021-11-17_03
2021-11-17_09
"""

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName=methodName)
        self.ascending_list = ['backup/blah_wps/2021/10/blah_wps_2021-10-10_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-11_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-12_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-13_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-14_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-15_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-20_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-21_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-22_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-29_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-30_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-10-31_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-01_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-02_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-13_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-14_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-15_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-16_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-17_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-18_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-19_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-20_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-21_14-00-10.sql.gz',
                               'backup/blah_wps/2021/10/blah_wps_2021-11-22_14-00-10.sql.gz']
        self.small_set = ['backup/blah_wps/2021/10/blah_wps_2021-10-21_14-00-10.sql.gz',
                          'backup/blah_wps/2021/10/blah_wps_2021-10-21_09-00-28.sql.gz',
                          'backup/blah_wps/2021/10/blah_wps_2021-10-21_03-00-25.sql.gz',
                          'backup/blah_wps/2021/10/blah_wps_2021-10-20_20-00-16.sql.gz']
        self.large_set = ['backup/blah_wps/2021/10/blah_wps_2021-10-21_14-00-10.sql.gz',  # 0 X
                          'backup/blah_wps/2021/10/blah_wps_2021-10-21_09-00-28.sql.gz',  # 1
                          'backup/blah_wps/2021/10/blah_wps_2021-10-21_03-00-25.sql.gz',  # 2
                          'backup/blah_wps/2021/10/blah_wps_2021-10-20_20-00-16.sql.gz',  # 3
                          'backup/blah_wps/2021/10/blah_wps_2021-10-19_20-00-16.sql.gz',  # 4 X
                          'backup/blah_wps/2021/10/blah_wps_2021-10-18_20-00-16.sql.gz',  # 5 X
                          'backup/blah_wps/2021/10/blah_wps_2021-10-17_20-00-16.sql.gz',  # 6 X
                          'backup/blah_wps/2021/10/blah_wps_2021-10-16_20-00-16.sql.gz',  # 7 X
                          'backup/blah_wps/2021/10/blah_wps_2021-10-15_20-00-16.sql.gz',  # 8
                          'backup/blah_wps/2021/10/blah_wps_2021-10-14_20-00-16.sql.gz',  # 9
                          'backup/blah_wps/2021/10/blah_wps_2021-10-13_20-00-16.sql.gz',  # 10 X
                          'backup/blah_wps/2021/10/blah_wps_2021-10-01_20-00-16.sql.gz',  # 11 X
                          'backup/blah_wps/2021/10/blah_wps_2021-09-20_20-00-16.sql.gz',  # 12 X
                          'backup/blah_wps/2021/10/blah_wps_2021-08-20_20-00-16.sql.gz',  # 13 X
                          'backup/blah_wps/2021/10/blah_wps_2021-07-20_20-00-16.sql.gz',  # 14 X
                          'backup/blah_wps/2021/10/blah_wps_2021-06-20_20-00-16.sql.gz',  # 15 x
                          'backup/blah_wps/2021/10/blah_wps_2021-05-20_20-00-16.sql.gz',  # 16
                          'backup/blah_wps/2021/10/blah_wps_2021-04-20_20-00-16.sql.gz',  # 17
                          'backup/blah_wps/2021/10/blah_wps_2021-03-20_20-00-16.sql.gz',  # 18
                          'backup/blah_wps/2021/10/blah_wps_2021-02-20_20-00-16.sql.gz',  # 19
                          'backup/blah_wps/2021/10/blah_wps_2020-12-20_20-00-16.sql.gz',  # 20
                          'backup/blah_wps/2021/10/blah_wps_2020-11-20_20-00-16.sql.gz',  # 21
                          'backup/blah_wps/2021/10/blah_wps_2019-10-20_20-00-16.sql.gz'  # 22
                          ]

    def test_a_number_of_days(self):
        """
        Test the number of days function

        1
        2
        3
        4
        5
        6
        7
        8
        9
        10


        """
        stamp = datetime(2020, 10, 15, 3, 0, 10)
        end = stamp + timedelta(weeks=52)
        # cronjob time increments, 3am, 9am, 2pm, 8pm.
        increment = [6, 5, 6, 7]
        files = []
        i = 0
        while stamp < end:
            i = i + 1
            new_file = stamp.strftime('backup/blah_wps/%Y/%m/blah_wps_%Y-%m-%d_%H-%M-%S.sql.gz')
            files.append(new_file)
            # print('files:')
            # for file in files:
            #     print(file)
            stamp += timedelta(hours=increment[i % 4])
            files = list(set(files).difference(decide_files_to_delete(files.copy())))

            files.sort()
        print('left over:')
        for file in files:
            print(file)
        # print(files.sort())
        self.assertEqual(len(files), 15)

    # def test_delete_sample_set(self):
    #     """ Test what should be deleted using an ascending list of files """
    #     files_to_delete = list(decide_files_to_delete(self.ascending_list.copy()))
    #     files_to_delete.sort()
    #     self.assertNotIn(self.ascending_list[-1], files_to_delete)
    #     self.assertNotIn(self.ascending_list[-2], files_to_delete)
    #     self.assertNotIn(self.ascending_list[-3], files_to_delete)
    #     self.assertNotIn(self.ascending_list[-4], files_to_delete)
    #     self.assertNotIn(self.ascending_list[-5], files_to_delete)

    # def test_keep_sample_set(self):
    #     """ Test what should be kept using an ascending list of files """
    #     files_to_keep = list(decide_files_to_keep(self.ascending_list.copy()))
    #     files_to_keep.sort()
    #     self.assertIn(self.ascending_list[-1], files_to_keep)
    #     self.assertIn(self.ascending_list[-2], files_to_keep)
    #     self.assertIn(self.ascending_list[-3], files_to_keep)
    #     self.assertIn(self.ascending_list[-4], files_to_keep)
    #     self.assertIn(self.ascending_list[-5], files_to_keep)

    # def test_keep_small_set(self):
    #     """ If there's nothing older than a day, we expect to retain up to 5 "hourly" values """
    #     files = self.small_set
    #     files_to_keep = decide_files_to_keep(files)
    #     self.assertEqual(len(files_to_keep), 4)
    #     self.assertIn(files[0], files_to_keep)

    # def test_delete_small_set(self):
    #     """ Check that delete works for smaller set """
    #     files = self.small_set
    #     files_to_delete = decide_files_to_delete(files)
    #     self.assertEqual(len(files_to_delete), 0)
    #     files_set = set(files)
    #     delete_set = set(files_to_delete)
    #     keep_set = set([files[0], files[1], files[2], files[3]])
    #     self.assertEqual(files_set.difference(keep_set), delete_set)

    # def test_keep_large_set(self):
    #     """ Check a larger set.
    #     """
    #     files = self.large_set
    #     files_to_keep = decide_files_to_keep(files)
    #     self.assertEqual(len(files_to_keep), 14)
    #     self.assertIn(files[0], files_to_keep)
    #     self.assertIn(files[1], files_to_keep)
    #     self.assertIn(files[2], files_to_keep)
    #     self.assertIn(files[3], files_to_keep)
    #     self.assertIn(files[4], files_to_keep)
    #     self.assertIn(files[5], files_to_keep)
    #     self.assertIn(files[6], files_to_keep)
    #     self.assertIn(files[7], files_to_keep)
    #     self.assertIn(files[10], files_to_keep)
    #     self.assertIn(files[11], files_to_keep)
    #     self.assertIn(files[12], files_to_keep)
    #     self.assertIn(files[13], files_to_keep)
    #     self.assertIn(files[14], files_to_keep)
    #     self.assertIn(files[15], files_to_keep)

    # def test_delete_large_set(self):
    #     """ Check that delete works for larger set """
    #     files = self.large_set
    #     files_to_delete = decide_files_to_delete(files)
    #     self.assertEqual(len(files_to_delete), 9)
    #     files_set = set(files)
    #     delete_set = set(files_to_delete)
    #     keep_set = set([files[0], files[1], files[2], files[3], files[4], files[5],
    #                     files[6], files[7], files[10],
    #                     files[11], files[12], files[13], files[14], files[15]])
    #     self.assertEqual(files_set.difference(keep_set), delete_set)


if __name__ == '__main__':
    unittest.main()
