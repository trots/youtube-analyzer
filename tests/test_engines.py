import unittest
from datetime import timedelta
from youtubeanalyzer.model import (ResultFields, ResultTableModel)
from youtubeanalyzer.engine import (
    timedelta_to_str, YoutubeApiEngine)


class MockYoutubeClient:
    """Minimal stub for the googleapiclient youtube resource, covering only videoCategories().list().execute()."""

    def __init__(self, category_responce):
        self._category_responce = category_responce

    def videoCategories(self):
        return self

    def list(self, **_kwargs):
        return self

    def execute(self):
        return self._category_responce


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
        self._category_responce = {
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
                    "medium": {
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
                    "medium": {
                        "url": "https://yt3.com/high2.png"
                    }
                }
            }
        })
        self._video_responce["items"].append({
            "id": "video1",
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
            "id": "video2",
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
        return MockYoutubeClient(self._category_responce)

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

    def _type(self, vid):
        return "longs"


class TestStringMethods(unittest.TestCase):

    def test_timedelta_to_str(self):
        self.assertEqual(timedelta_to_str(timedelta(seconds=0)), "00:00:00")
        self.assertEqual(timedelta_to_str(timedelta(seconds=671)), "00:11:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=3671)), "01:01:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=90671)), "1:01:11:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=900671)), "10:10:11:11")
        self.assertEqual(timedelta_to_str(timedelta(seconds=9000671)), "104:04:11:11")

        self.assertEqual(timedelta_to_str(None), "")

    def test_youtube_api_engine(self):
        engine = MockApiEngine()
        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 2)

        self.assertEqual(model.get_field_data(0, ResultFields.VideoTitle), "First video")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoPublishedTime), "2024-06-05 13:01:03")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoDuration), "00:16:40")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoViews), 589025)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoLink), "https://www.youtube.com/watch?v=video1")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelTitle), "First channel")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelLink), "https://www.youtube.com/channel/channel1")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelSubscribers), 77900)
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelJoinedDate), "")
        self.assertEqual(model.get_field_data(0, ResultFields.ViewRate), "756.13%")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoPreviewLink), "https://yt3.com/high1.png")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelLogoLink), "http://yt3.com/default1.png")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoTags), ["word1", "word2"])
        self.assertEqual(model.get_field_data(0, ResultFields.VideoDurationTimedelta), timedelta(seconds=1000))

        self.assertEqual(model.get_field_data(1, ResultFields.VideoTitle), "Second video")
        self.assertEqual(model.get_field_data(1, ResultFields.VideoPublishedTime), "2023-04-12 15:12:43")
        self.assertEqual(model.get_field_data(1, ResultFields.VideoDuration), "00:24:31")
        self.assertEqual(model.get_field_data(1, ResultFields.VideoViews), 1598)
        self.assertEqual(model.get_field_data(1, ResultFields.VideoLink), "https://www.youtube.com/watch?v=video2")
        self.assertEqual(model.get_field_data(1, ResultFields.ChannelTitle), "Second channel")
        self.assertEqual(model.get_field_data(1, ResultFields.ChannelLink), "https://www.youtube.com/channel/channel2")
        self.assertEqual(model.get_field_data(1, ResultFields.ChannelSubscribers), 734)
        self.assertEqual(model.get_field_data(1, ResultFields.ChannelJoinedDate), "")
        self.assertEqual(model.get_field_data(1, ResultFields.ViewRate), "217.71%")
        self.assertEqual(model.get_field_data(1, ResultFields.VideoPreviewLink), "https://yt3.com/high2.png")
        self.assertEqual(model.get_field_data(1, ResultFields.ChannelLogoLink), "http://yt3.com/default2.png")
        self.assertEqual(model.get_field_data(1, ResultFields.VideoTags), ["word2", "word3"])
        self.assertEqual(model.get_field_data(1, ResultFields.VideoDurationTimedelta), timedelta(seconds=1471))

    def test_youtube_api_engine_failures(self):
        engine = MockApiEngine(empty=True)
        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 0)

        engine = MockApiEngine(exception=True)
        self.assertFalse(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 0)

    def test_youtube_api_engine_skips_video_without_id(self):
        engine = MockApiEngine(empty=True)
        engine._search_responce["items"].append({
            "id": {
                "kind": "youtube#video",
                "videoId": "video1"
            },
            "snippet": {
                "title": "First video",
                "publishTime": "2024-06-05T13:01:03Z",
                "channelId": "channel1",
                "channelTitle": "First channel"
            }
        })
        # A real-world case: the search response occasionally contains a channel entry
        # instead of a video. It has an "id", but no nested "videoId".
        engine._search_responce["items"].append({
            "id": {
                "kind": "youtube#channel",
                "channelId": "channelX"
            },
            "snippet": {
                "title": "A channel that leaked into search results",
                "channelId": "channelX"
            }
        })
        engine._video_responce["items"].append({
            "id": "video1",
            "contentDetails": {"duration": "PT16M40S"},
            "statistics": {"viewCount": "589025"},
            "snippet": {"tags": ["word1", "word2"]}
        })
        engine._channel_responce["items"].append({
            "id": "channel1",
            "statistics": {"viewCount": "76177771", "subscriberCount": "77900"},
            "snippet": {}
        })

        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoTitle), "First video")
        self.assertEqual(len(engine.warnings), 1)

    def test_youtube_api_engine_skips_video_without_details(self):
        engine = MockApiEngine(empty=True)
        engine._search_responce["items"].append({
            "id": {"videoId": "video1"},
            "snippet": {
                "title": "First video",
                "publishTime": "2024-06-05T13:01:03Z",
                "channelId": "channel1",
                "channelTitle": "First channel"
            }
        })
        engine._search_responce["items"].append({
            "id": {"videoId": "video2"},
            "snippet": {
                "title": "Second video",
                "publishTime": "2023-04-12T15:12:43Z",
                "channelId": "channel2",
                "channelTitle": "Second channel"
            }
        })
        # video2 disappeared (deleted/region-blocked) by the time details are fetched.
        engine._video_responce["items"].append({
            "id": "video1",
            "contentDetails": {"duration": "PT16M40S"},
            "statistics": {"viewCount": "589025"},
            "snippet": {"tags": ["word1", "word2"]}
        })
        engine._channel_responce["items"].append({
            "id": "channel1",
            "statistics": {"viewCount": "76177771", "subscriberCount": "77900"},
            "snippet": {}
        })

        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoTitle), "First video")
        self.assertEqual(len(engine.warnings), 1)

    def test_youtube_api_engine_skips_video_without_snippet(self):
        engine = MockApiEngine(empty=True)
        engine._search_responce["items"].append({
            "id": {"videoId": "video1"}
            # "snippet" is missing entirely
        })
        engine._search_responce["items"].append({
            "id": {"videoId": "video2"},
            "snippet": {
                "title": "Second video",
                "publishTime": "2023-04-12T15:12:43Z",
                "channelId": "channel2",
                "channelTitle": "Second channel"
            }
        })
        engine._video_responce["items"].append({"id": "video1"})
        engine._video_responce["items"].append({"id": "video2"})

        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoTitle), "Second video")
        self.assertEqual(len(engine.warnings), 1)

    def test_youtube_api_engine_missing_top_level_items(self):
        engine = MockApiEngine(empty=True)
        engine._search_responce = {}  # no "items" key at all

        self.assertFalse(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 0)
        self.assertTrue(engine.errorDetails)

    def test_youtube_api_engine_missing_optional_fields_uses_defaults(self):
        engine = MockApiEngine(empty=True)
        engine._search_responce["items"].append({
            "id": {"videoId": "video1"},
            "snippet": {}
            # no title, publishTime, channelId, channelTitle, thumbnails
        })
        engine._video_responce["items"].append({
            "id": "video1"
            # no contentDetails, statistics, snippet
        })

        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(len(engine.warnings), 0)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoTitle), "")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoPublishedTime), "")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoDuration), "00:00:00")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoDurationTimedelta), timedelta(seconds=0))
        self.assertEqual(model.get_field_data(0, ResultFields.VideoViews), 0)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoLink), "https://www.youtube.com/watch?v=video1")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelTitle), "")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelLink), "")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelSubscribers), 0)
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelJoinedDate), "")
        self.assertEqual(model.get_field_data(0, ResultFields.ViewRate), "-")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoPreviewLink), "")
        self.assertEqual(model.get_field_data(0, ResultFields.ChannelLogoLink), "")
        self.assertEqual(model.get_field_data(0, ResultFields.VideoTags), [])

    def test_youtube_api_engine_thumbnail_fallback(self):
        engine = MockApiEngine(empty=True)
        engine._search_responce["items"].append({
            "id": {"videoId": "video1"},
            "snippet": {
                "thumbnails": {
                    "high": {"url": "https://yt3.com/high1.png"}
                }
            }
        })
        engine._search_responce["items"].append({
            "id": {"videoId": "video2"},
            "snippet": {
                "thumbnails": {
                    "default": {"url": "https://yt3.com/default2.png"}
                }
            }
        })
        engine._video_responce["items"].append({"id": "video1"})
        engine._video_responce["items"].append({"id": "video2"})

        self.assertTrue(engine.search("request"))
        model = engine.model()
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.get_field_data(0, ResultFields.VideoPreviewLink), "https://yt3.com/high1.png")
        self.assertEqual(model.get_field_data(1, ResultFields.VideoPreviewLink), "https://yt3.com/default2.png")

    def test_youtube_api_engine_video_categories_skips_invalid_and_defaults_title(self):
        engine = MockApiEngine(empty=True)
        engine._category_responce["items"].append({
            "id": "1",
            "snippet": {"title": "Film & Animation"}
        })
        # Missing "id" and "snippet" entirely - should be skipped.
        engine._category_responce["items"].append({
            "kind": "youtube#videoCategory"
        })
        engine._category_responce["items"].append({
            "id": "2",
            "snippet": {}
            # missing "title" -> defaults to ""
        })

        categories = engine.get_video_categories()

        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0].id, "1")
        self.assertEqual(categories[0].text, "Film & Animation")
        self.assertEqual(categories[1].id, "2")
        self.assertEqual(categories[1].text, "")
        self.assertEqual(len(engine.warnings), 1)

    def test_youtube_api_engine_video_categories_missing_items(self):
        engine = MockApiEngine(empty=True)
        engine._category_responce = {}  # no "items" key at all

        categories = engine.get_video_categories()

        self.assertEqual(categories, [])
        self.assertTrue(engine.errorDetails)


if __name__ == "__main__":
    unittest.main()
