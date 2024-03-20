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

if __name__ == "__main__":
    unittest.main()
