import unittest
from datetime import timedelta
from engine import (timedelta_to_str, YoutubeGrepEngine)

class TestStringMethods(unittest.TestCase):

    def test_timedelta_to_str(self):
        self.assertEqual(timedelta_to_str(timedelta(seconds=0)), "00:00:00")
        self.assertEqual(timedelta_to_str(timedelta(seconds=671)), "00:11:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=3671)), "01:01:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=90671)), "1:01:11:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=900671)), "10:10:11:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=9000671)), "104:04:11:11")

        self.assertEqual(timedelta_to_str(None), "")

    def test_youtube_grep_duration_converter(self):
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("0:01")), "00:00:01")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("1:01")), "00:01:01")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("10:01")), "00:10:01")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("1:10:01")), "01:10:01")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("10:10:01")), "10:10:01")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("100:10:01")), "4:04:10:01")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.duration_to_timedelta("1000:10:01")), "41:16:10:01")

        self.assertIsNone(YoutubeGrepEngine.duration_to_timedelta(""))
        self.assertIsNone(YoutubeGrepEngine.duration_to_timedelta(None))
        self.assertIsNone(YoutubeGrepEngine.duration_to_timedelta("0"))
        self.assertIsNone(YoutubeGrepEngine.duration_to_timedelta("0:0:0:0"))

    def test_youtube_grep_publish_time_converter(self):
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("54 seconds ago")), "00:00:54")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("25 minutes ago")), "00:25:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("16 hours ago")), "16:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("3 days ago")), "3:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("2 weeks ago")), "14:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("4 months ago")), "120:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("3 years ago")), "1080:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("Streamed 3 years ago")), "1080:00:00:00")

        self.assertIsNone(YoutubeGrepEngine.published_time_to_timedelta(""))
        self.assertIsNone(YoutubeGrepEngine.published_time_to_timedelta(None))
        self.assertIsNone(YoutubeGrepEngine.published_time_to_timedelta("0"))
        self.assertIsNone(YoutubeGrepEngine.published_time_to_timedelta("1 part ago"))

    def test_youtube_grep_publish_time_sort_cast(self):
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("54 seconds ago"), 54)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("25 minutes ago"), 2500)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("16 hours ago"), 160000)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("3 days ago"), 3000000)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("2 weeks ago"), 14000000)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("4 months ago"), 120000000)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("3 years ago"), 1080000000)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("9 years ago"), 3240000000)
        self.assertEqual(YoutubeGrepEngine.published_time_sort_cast("Streamed 3 years ago"), 1080000000)

        self.assertIsNone(YoutubeGrepEngine.published_time_sort_cast(""))
        self.assertIsNone(YoutubeGrepEngine.published_time_sort_cast(None))
        self.assertIsNone(YoutubeGrepEngine.published_time_sort_cast("0"))
        self.assertIsNone(YoutubeGrepEngine.published_time_sort_cast("1 part ago"))

if __name__ == "__main__":
    unittest.main()
