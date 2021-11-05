""" Tests for prune.py
"""
import unittest
from prune import decide_files_to_keep, decide_files_to_delete


class TestPrune(unittest.TestCase):
    """ Unit tests for prune.py """

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

    def test_delete_sample_set(self):
        """ """
        files_to_delete = list(decide_files_to_delete(self.ascending_list.copy()))
        files_to_delete.sort()
        self.assertNotIn(self.ascending_list[-1], files_to_delete)
        self.assertNotIn(self.ascending_list[-2], files_to_delete)
        self.assertNotIn(self.ascending_list[-3], files_to_delete)
        self.assertNotIn(self.ascending_list[-4], files_to_delete)
        self.assertNotIn(self.ascending_list[-5], files_to_delete)

    def test_keep_sample_set(self):
        files_to_keep = list(decide_files_to_keep(self.ascending_list.copy()))
        files_to_keep.sort()
        self.assertIn(self.ascending_list[-1], files_to_keep)
        self.assertIn(self.ascending_list[-2], files_to_keep)
        self.assertIn(self.ascending_list[-3], files_to_keep)
        self.assertIn(self.ascending_list[-4], files_to_keep)
        self.assertIn(self.ascending_list[-5], files_to_keep)

    def test_keep_small_set(self):
        """ We only care about the most recent backup if there's nothing older than a day """
        files = self.small_set
        files_to_keep = decide_files_to_keep(files)
        self.assertEqual(len(files_to_keep), 1)
        self.assertIn(files[0], files_to_keep)

    def test_delete_small_set(self):
        """ Check that delete works for smaller set """
        files = self.small_set
        files_to_delete = decide_files_to_delete(files)
        self.assertEqual(len(files_to_delete), 3)
        files_set = set(files)
        delete_set = set(files_to_delete)
        keep_set = set([files[0]])
        self.assertEqual(files_set.difference(keep_set), delete_set)

    def test_keep_large_set(self):
        """ Check a larger set.
        """
        files = self.large_set
        files_to_keep = decide_files_to_keep(files)
        self.assertEqual(len(files_to_keep), 11)
        self.assertIn(files[0], files_to_keep)
        self.assertIn(files[4], files_to_keep)
        self.assertIn(files[5], files_to_keep)
        self.assertIn(files[6], files_to_keep)
        self.assertIn(files[7], files_to_keep)
        self.assertIn(files[10], files_to_keep)
        self.assertIn(files[11], files_to_keep)
        self.assertIn(files[12], files_to_keep)
        self.assertIn(files[13], files_to_keep)
        self.assertIn(files[14], files_to_keep)
        self.assertIn(files[15], files_to_keep)

    def test_delete_large_set(self):
        """ Check that delete works for larger set """
        files = self.large_set
        files_to_delete = decide_files_to_delete(files)
        self.assertEqual(len(files_to_delete), 12)
        files_set = set(files)
        delete_set = set(files_to_delete)
        keep_set = set([files[0], files[4], files[5], files[6], files[7], files[10],
                        files[11], files[12], files[13], files[14], files[15]])
        self.assertEqual(files_set.difference(keep_set), delete_set)


if __name__ == '__main__':
    unittest.main()
