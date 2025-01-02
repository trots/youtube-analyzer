import unittest
from datetime import timedelta
from youtubeanalyzer.model import (ResultFields, ResultTableModel)
from youtubeanalyzer.engine import (
    timedelta_to_str, view_count_to_int, subcriber_count_to_int,
    YoutubeGrepEngine, YoutubeApiEngine)


class MockVideosSearch:
    def __init__(self, request_limit: int):
        self._request_limit = min(request_limit, 3)
        self._has_next = True if request_limit == 3 else False
        self._result = {
            "result": []
        }
        if request_limit > 0:
            self._result["result"].append({
                "title": "First video",
                "id": "1",
                "duration": "12:34",
                "publishedTime": "8 hours ago",
                "link": "https://video_1",
                "viewCount": {
                    "text": "123 views"
                },
                "channel": {
                    "id": "1"
                },
                "thumbnails": [
                    {
                        "url": "https://thumb_1.png"
                    }
                ]
            })
        if request_limit > 1:
            self._result["result"].append({
                "title": "Second video",
                "id": "2",
                "duration": "23:12",
                "publishedTime": "3 hours ago",
                "link": "https://video_2",
                "viewCount": {
                    "text": "800 views"
                },
                "channel": {
                    "id": "2"
                },
                "thumbnails": [
                    {
                        "url": "https://thumb_2.png"
                    }
                ]
            })

    def next(self):
        has_next = self._has_next
        self._has_next = False

        if has_next:
            self._result = {
                "result": [
                    {
                        "title": "Third video",
                        "id": "3",
                        "duration": "36:47",
                        "publishedTime": "10 hours ago",
                        "link": "https://video_3",
                        "viewCount": {
                            "text": "409 views"
                        },
                        "channel": {
                            "id": "3"
                        },
                        "thumbnails": [
                            {
                                "url": "https://thumb_3.png"
                            }
                        ]
                    }
                ]
            }
        return has_next

    def result(self):
        return self._result


class MockGrepEngine(YoutubeGrepEngine):
    def __init__(self, request_limit: int, exception=False):
        super().__init__(ResultTableModel(None), request_limit)
        self._exception = exception

    def model(self):
        return self._model

    def _create_video_searcher(self, _request_text):
        if self._exception:
            raise "Exception"
        return MockVideosSearch(self._request_limit)

    def _get_video_info(self, _video_id: str):
        return {
            "keywords": ["word1", "word2"]
        }

    def _get_channel_info(self, _channel_id: str):
        return {
            "title": "First channel title",
            "url": "https://fchannel",
            "views": "895 views",
            "joinedDate": "2020-05-18",
            "subscribers": {
                "simpleText": "30 subscribers"
            },
            "thumbnails": [
                {
                    "url": "https://logo_1.png"
                }
            ]
        }


class MockApiEngine(YoutubeApiEngine):
    def __init__(self, empty=False, exception=False):
        super().__init__("", ResultTableModel(None), 2)
        self._exception = exception
        self._search_responce = {
            "items": []
        }
        self._video_responce = {
            "items": []
        }
        self._channel_responce = {
            "items": []
        }
        if empty:
            return
        self._search_responce["items"].append({
            "id": {
                "videoId": "video1"
            },
            "snippet": {
                "title": "First video",
                "publishTime": "2024-06-05T13:01:03Z",
                "channelId": "channel1",
                "channelTitle": "First channel",
                "thumbnails": {
                    "high": {
                        "url": "https://yt3.com/high1.png"
                    }
                }
            }
        })
        self._search_responce["items"].append({
            "id": {
                "videoId": "video2"
            },
            "snippet": {
                "title": "Second video",
                "publishTime": "2023-04-12T15:12:43Z",
                "channelId": "channel2",
                "channelTitle": "Second channel",
                "thumbnails": {
                    "high": {
                        "url": "https://yt3.com/high2.png"
                    }
                }
            }
        })
        self._video_responce["items"].append({
            "contentDetails": {
                "duration": "PT16M40S"
            },
            "statistics": {
                "viewCount": "589025"
            },
            "snippet": {
                "tags": ["word1", "word2"]
            }
        })
        self._video_responce["items"].append({
            "contentDetails": {
                "duration": "PT24M31S"
            },
            "statistics": {
                "viewCount": "1598"
            },
            "snippet": {
                "tags": ["word2", "word3"]
            }
        })
        self._channel_responce["items"].append({
            "id": "channel1",
            "statistics": {
                "viewCount": "76177771",
                "subscriberCount": "77900"
            },
            "snippet": {
                "thumbnails": {
                    "default": {
                        "url": "https://yt3.com/default1.png"
                    }
                }
            }
        })
        self._channel_responce["items"].append({
            "id": "channel2",
            "statistics": {
                "viewCount": "789025",
                "subscriberCount": "734"
            },
            "snippet": {
                "thumbnails": {
                    "default": {
                        "url": "https://yt3.com/default2.png"
                    }
                }
            }
        })

    def model(self):
        return self._model

    def _create_youtube_client(self):
        return None

    def _request_videos(self, request_handler, video_id_getter, published_time_key):
        if self._exception:
            raise "Exception"

        def mock_request_handler(youtube, page_token):
            return self._search_responce
        return super()._request_videos(mock_request_handler, video_id_getter, published_time_key)

    def _get_video_details(self, _youtube, _video_ids):
        return self._video_responce

    def _get_channel_details(self, _youtube, _channel_ids):
        return self._channel_responce


class TestStringMethods(unittest.TestCase):

    def test_view_count_to_int(self):
        self.assertEqual(view_count_to_int("123"), 123)
        self.assertEqual(view_count_to_int("629 views"), 629)
        self.assertEqual(view_count_to_int("578,614 views"), 578614)
        self.assertEqual(view_count_to_int("22,112,475 views"), 22112475)

        self.assertEqual(view_count_to_int(None), 0)
        self.assertEqual(view_count_to_int(""), 0)

    def test_subscriber_count_to_int(self):
        self.assertEqual(subcriber_count_to_int("1 subscriber"), 1)
        self.assertEqual(subcriber_count_to_int("640 subscribers"), 640)
        self.assertEqual(subcriber_count_to_int("11K subscribers"), 11000)
        self.assertEqual(subcriber_count_to_int("11.5K subscribers"), 11500)
        self.assertEqual(subcriber_count_to_int("17M subscribers"), 17000000)
        self.assertEqual(subcriber_count_to_int("17.3M subscribers"), 17300000)
        self.assertEqual(subcriber_count_to_int("3B subscribers"), 3000000000)
        self.assertEqual(subcriber_count_to_int("3.5B subscribers"), 3500000000)

        self.assertEqual(subcriber_count_to_int(None), 0)
        self.assertEqual(subcriber_count_to_int(""), 0)

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

        self.assertEqual(YoutubeGrepEngine.duration_to_timedelta(""), timedelta(seconds=0))
        self.assertEqual(YoutubeGrepEngine.duration_to_timedelta(None), timedelta(seconds=0))
        self.assertEqual(YoutubeGrepEngine.duration_to_timedelta("0"), timedelta(seconds=0))
        self.assertEqual(YoutubeGrepEngine.duration_to_timedelta("0:0:0:0"), timedelta(seconds=0))

    def test_youtube_grep_publish_time_converter(self):
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("54 seconds ago")), "00:00:54")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("25 minutes ago")), "00:25:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("16 hours ago")), "16:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("3 days ago")), "3:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("2 weeks ago")), "14:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("4 months ago")), "120:00:00:00")
        self.assertEqual(timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("3 years ago")), "1080:00:00:00")
        self.assertEqual(
            timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta("Streamed 3 years ago")), "1080:00:00:00")

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

    def test_youtube_grep_engine(self):
        for count in range(4):
            engine = MockGrepEngine(count)
            self.assertTrue(engine.search("request"))
            model = engine.model()
            self.assertEqual(len(model.result), count)

            if count > 0:
                self.assertEqual(model.result[0][ResultFields.VideoTitle], "First video")
                self.assertEqual(model.result[0][ResultFields.VideoPublishedTime], "8 hours ago")
                self.assertEqual(model.result[0][ResultFields.VideoDuration], "00:12:34")
                self.assertEqual(model.result[0][ResultFields.VideoViews], 123)
                self.assertEqual(model.result[0][ResultFields.VideoLink], "https://video_1")
                self.assertEqual(model.result[0][ResultFields.ChannelTitle], "First channel title")
                self.assertEqual(model.result[0][ResultFields.ChannelLink], "https://fchannel")
                self.assertEqual(model.result[0][ResultFields.ChannelSubscribers], 30)
                self.assertEqual(model.result[0][ResultFields.ChannelJoinedDate], "2020-05-18")
                self.assertEqual(model.result[0][ResultFields.ViewRate], "410.0%")
                self.assertEqual(model.result[0][ResultFields.VideoPreviewLink], "https://thumb_1.png")
                self.assertEqual(model.result[0][ResultFields.ChannelLogoLink], "https://logo_1.png")
                self.assertEqual(model.result[0][ResultFields.VideoTags], ["word1", "word2"])
                self.assertEqual(model.result[0][ResultFields.VideoDurationTimedelta], timedelta(seconds=754))
            if count > 1:
                self.assertEqual(model.result[1][ResultFields.VideoTitle], "Second video")
                self.assertEqual(model.result[1][ResultFields.VideoPublishedTime], "3 hours ago")
                self.assertEqual(model.result[1][ResultFields.VideoDuration], "00:23:12")
                self.assertEqual(model.result[1][ResultFields.VideoViews], 800)
                self.assertEqual(model.result[1][ResultFields.VideoLink], "https://video_2")
                self.assertEqual(model.result[1][ResultFields.ChannelTitle], "First channel title")
                self.assertEqual(model.result[1][ResultFields.ChannelLink], "https://fchannel")
                self.assertEqual(model.result[1][ResultFields.ChannelSubscribers], 30)
                self.assertEqual(model.result[1][ResultFields.ChannelJoinedDate], "2020-05-18")
                self.assertEqual(model.result[1][ResultFields.ViewRate], "2666.67%")
                self.assertEqual(model.result[1][ResultFields.VideoPreviewLink], "https://thumb_2.png")
                self.assertEqual(model.result[1][ResultFields.ChannelLogoLink], "https://logo_1.png")
                self.assertEqual(model.result[1][ResultFields.VideoTags], ["word1", "word2"])
                self.assertEqual(model.result[1][ResultFields.VideoDurationTimedelta], timedelta(seconds=1392))
            if count > 2:
                self.assertEqual(model.result[2][ResultFields.VideoTitle], "Third video")
                self.assertEqual(model.result[2][ResultFields.VideoPublishedTime], "10 hours ago")
                self.assertEqual(model.result[2][ResultFields.VideoDuration], "00:36:47")
                self.assertEqual(model.result[2][ResultFields.VideoViews], 409)
                self.assertEqual(model.result[2][ResultFields.VideoLink], "https://video_3")
                self.assertEqual(model.result[2][ResultFields.ChannelTitle], "First channel title")
                self.assertEqual(model.result[2][ResultFields.ChannelLink], "https://fchannel")
                self.assertEqual(model.result[2][ResultFields.ChannelSubscribers], 30)
                self.assertEqual(model.result[2][ResultFields.ChannelJoinedDate], "2020-05-18")
                self.assertEqual(model.result[2][ResultFields.ViewRate], "1363.33%")
                self.assertEqual(model.result[2][ResultFields.VideoPreviewLink], "https://thumb_3.png")
                self.assertEqual(model.result[2][ResultFields.ChannelLogoLink], "https://logo_1.png")
                self.assertEqual(model.result[2][ResultFields.VideoTags], ["word1", "word2"])
                self.assertEqual(model.result[2][ResultFields.VideoDurationTimedelta], timedelta(seconds=2207))

    def test_youtube_grep_engine_failures(self):
        engine = MockGrepEngine(0)
        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(len(model.result), 0)

        engine = MockGrepEngine(1, exception=True)
        self.assertFalse(engine.search("request"))
        model = engine.model()
        self.assertEqual(len(model.result), 0)

    def test_youtube_api_engine(self):
        engine = MockApiEngine()
        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(len(model.result), 2)

        self.assertEqual(model.result[0][ResultFields.VideoTitle], "First video")
        self.assertEqual(model.result[0][ResultFields.VideoPublishedTime], "2024-06-05 13:01:03")
        self.assertEqual(model.result[0][ResultFields.VideoDuration], "00:16:40")
        self.assertEqual(model.result[0][ResultFields.VideoViews], 589025)
        self.assertEqual(model.result[0][ResultFields.VideoLink], "https://www.youtube.com/watch?v=video1")
        self.assertEqual(model.result[0][ResultFields.ChannelTitle], "First channel")
        self.assertEqual(model.result[0][ResultFields.ChannelLink], "https://www.youtube.com/channel/channel1")
        self.assertEqual(model.result[0][ResultFields.ChannelSubscribers], 77900)
        self.assertEqual(model.result[0][ResultFields.ChannelJoinedDate], "")
        self.assertEqual(model.result[0][ResultFields.ViewRate], "756.13%")
        self.assertEqual(model.result[0][ResultFields.VideoPreviewLink], "https://yt3.com/high1.png")
        self.assertEqual(model.result[0][ResultFields.ChannelLogoLink], "http://yt3.com/default1.png")
        self.assertEqual(model.result[0][ResultFields.VideoTags], ["word1", "word2"])
        self.assertEqual(model.result[0][ResultFields.VideoDurationTimedelta], timedelta(seconds=1000))

        self.assertEqual(model.result[1][ResultFields.VideoTitle], "Second video")
        self.assertEqual(model.result[1][ResultFields.VideoPublishedTime], "2023-04-12 15:12:43")
        self.assertEqual(model.result[1][ResultFields.VideoDuration], "00:24:31")
        self.assertEqual(model.result[1][ResultFields.VideoViews], 1598)
        self.assertEqual(model.result[1][ResultFields.VideoLink], "https://www.youtube.com/watch?v=video2")
        self.assertEqual(model.result[1][ResultFields.ChannelTitle], "Second channel")
        self.assertEqual(model.result[1][ResultFields.ChannelLink], "https://www.youtube.com/channel/channel2")
        self.assertEqual(model.result[1][ResultFields.ChannelSubscribers], 734)
        self.assertEqual(model.result[1][ResultFields.ChannelJoinedDate], "")
        self.assertEqual(model.result[1][ResultFields.ViewRate], "217.71%")
        self.assertEqual(model.result[1][ResultFields.VideoPreviewLink], "https://yt3.com/high2.png")
        self.assertEqual(model.result[1][ResultFields.ChannelLogoLink], "http://yt3.com/default2.png")
        self.assertEqual(model.result[1][ResultFields.VideoTags], ["word2", "word3"])
        self.assertEqual(model.result[1][ResultFields.VideoDurationTimedelta], timedelta(seconds=1471))

    def test_youtube_api_engine_failures(self):
        engine = MockApiEngine(empty=True)
        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(len(model.result), 0)

        engine = MockApiEngine(exception=True)
        self.assertFalse(engine.search("request"))
        model = engine.model()
        self.assertEqual(len(model.result), 0)


if __name__ == "__main__":
    unittest.main()
