import os

if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from datetime import timedelta
from PySide6.QtCore import Qt
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel,
    make_result_row
)


def create_model(video_published_time="2020-05-18 10:20:30", views=1234567, channel_subscribers=234567,
                 video_title="Video Title", channel_title="Channel Title"):
    result = [make_result_row(
        video_title, video_published_time, "00:34", views, "https://video1", channel_title, "https://channel1",
        channel_subscribers, 12345, "2020-05-18", "https://preview1.jpg", "https://logo1.jpg",
        ["word1", "word2"], timedelta(seconds=34), 0, "shorts", [])]
    model = ResultTableModel(None)
    model.set_data(result)
    return model


def video_title_display(model: ResultTableModel) -> str:
    column = model.map_field_to_table_column(ResultFields.VideoTitle)
    index = model.index(0, column)
    return model.data(index, Qt.ItemDataRole.DisplayRole)


class TestResultTableModelGalleryDisplay(unittest.TestCase):

    def test_normal_mode_video_title_display_role_is_none(self):
        model = create_model()
        model.set_mode(ResultTableModel.Mode.Normal)
        self.assertIsNone(video_title_display(model))

    def test_image_mode_video_title_display_role_includes_stats_lines(self):
        model = create_model(video_published_time="2020-05-18 10:20:30", views=1234567,
                             channel_subscribers=234567, video_title="Video Title",
                             channel_title="Channel Title")
        model.set_mode(ResultTableModel.Mode.Image)

        display_text = video_title_display(model)
        lines = display_text.split("\n")

        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], "Video Title")
        self.assertEqual(lines[1], "Channel Title")
        self.assertEqual(lines[2], "234 567 subscribers")
        self.assertEqual(lines[3], "1 234 567 views · 2020-05-18")

    def test_image_mode_published_date_from_api_format_is_truncated_to_date(self):
        model = create_model(video_published_time="2021-01-02 03:04:05")
        model.set_mode(ResultTableModel.Mode.Image)

        display_text = video_title_display(model)

        self.assertIn("2021-01-02", display_text.split("\n")[3])
        self.assertNotIn("03:04:05", display_text)

    def test_image_mode_published_date_falls_back_to_raw_text_for_non_standard_format(self):
        model = create_model(video_published_time="8 hours ago")
        model.set_mode(ResultTableModel.Mode.Image)

        display_text = video_title_display(model)

        self.assertEqual(display_text.split("\n")[3], "1 234 567 views · 8 hours ago")

    def test_format_published_date_directly(self):
        model = create_model()

        self.assertEqual(model._format_published_date(""), "")
        self.assertEqual(model._format_published_date("2020-05-18 10:20:30"), "2020-05-18")
        self.assertEqual(model._format_published_date("8 hours ago"), "8 hours ago")


if __name__ == "__main__":
    unittest.main()
