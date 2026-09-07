import os

if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from datetime import datetime, timedelta
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
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


def video_title_role_data(model: ResultTableModel, role: int):
    column = model.map_field_to_table_column(ResultFields.VideoTitle)
    index = model.index(0, column)
    return model.data(index, role)


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
        model.set_preview_scale(3.0)  # wide enough that no stats line needs eliding

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
        model.set_preview_scale(3.0)  # wide enough that no stats line needs eliding

        display_text = video_title_display(model)

        self.assertIn("2021-01-02", display_text.split("\n")[3])
        self.assertNotIn("03:04:05", display_text)

    def test_image_mode_published_date_falls_back_to_raw_text_for_non_standard_format(self):
        model = create_model(video_published_time="8 hours ago")
        model.set_mode(ResultTableModel.Mode.Image)
        model.set_preview_scale(3.0)  # wide enough that no stats line needs eliding

        display_text = video_title_display(model)

        self.assertEqual(display_text.split("\n")[3], "1 234 567 views · 8 hours ago")

    def test_image_mode_stats_lines_are_elided_when_too_narrow_for_the_card(self):
        # At the default preview scale the card is narrower than a typical stats line - each
        # of channel/subscribers/views lines must stay on one physical line (never wrap), so
        # they get elided instead, just like the title already is.
        model = create_model(views=1234567, channel_subscribers=234567, channel_title="Channel Title")
        model.set_mode(ResultTableModel.Mode.Image)

        display_text = video_title_display(model)
        lines = display_text.split("\n")

        self.assertEqual(len(lines), 4)
        self.assertIn("…", lines[2])
        self.assertIn("…", lines[3])

    def test_format_published_date_directly(self):
        model = create_model()

        self.assertEqual(model._format_published_date(""), "")
        self.assertEqual(model._format_published_date("2020-05-18 10:20:30"), "2020-05-18")
        self.assertEqual(model._format_published_date("8 hours ago"), "8 hours ago")

    def test_image_mode_video_link_role_returns_video_link(self):
        model = create_model()
        model.set_mode(ResultTableModel.Mode.Image)

        self.assertEqual(video_title_role_data(model, ResultTableModel.VideoLinkRole), "https://video1")

    def test_image_mode_channel_link_role_returns_channel_link(self):
        model = create_model()
        model.set_mode(ResultTableModel.Mode.Image)

        self.assertEqual(video_title_role_data(model, ResultTableModel.ChannelLinkRole), "https://channel1")

    def test_normal_mode_video_link_role_is_none(self):
        model = create_model()
        model.set_mode(ResultTableModel.Mode.Normal)

        self.assertIsNone(video_title_role_data(model, ResultTableModel.VideoLinkRole))

    def test_normal_mode_channel_link_role_is_none(self):
        model = create_model()
        model.set_mode(ResultTableModel.Mode.Normal)

        self.assertIsNone(video_title_role_data(model, ResultTableModel.ChannelLinkRole))

    def test_elide_two_lines_bold_flag_uses_bold_font_metrics(self):
        model = create_model()
        text = "A moderately long video title used to compare bold and regular width"
        width = 200

        # Force a distinctly different metrics object for the bold path, to verify that
        # `bold=True` actually selects `_bold_font_metrics` instead of `_font_metrics`
        # (real bold/regular glyph widths may be identical under some headless/offscreen
        # font backends, which would make this test unreliable without the override).
        model._bold_font_metrics = QFontMetrics(QFont("Sans Serif", 40))

        regular = model._elide_two_lines(text, width, bold=False)
        bold = model._elide_two_lines(text, width, bold=True)

        self.assertNotEqual(regular, bold)


class TestGetFieldForColumn(unittest.TestCase):

    def test_get_field_for_column_is_inverse_of_map_field_to_table_column(self):
        model = create_model()

        for column in range(model.columnCount()):
            field = model.get_field_for_column(column)
            self.assertEqual(model.map_field_to_table_column(field), column)

    def test_get_field_for_column_matches_default_table_columns(self):
        model = create_model()

        columns = [model.get_field_for_column(column) for column in range(model.columnCount())]

        self.assertEqual(columns, [
            ResultFields.VideoRelevanceNumber,
            ResultFields.VideoTitle,
            ResultFields.VideoPublishedTime,
            ResultFields.VideoDuration,
            ResultFields.VideoViews,
            ResultFields.ChannelTitle,
            ResultFields.ChannelSubscribers,
            ResultFields.ViewRate,
        ])


class TestResultTableModelFetchedAt(unittest.TestCase):

    def test_get_fetched_at_is_none_before_any_data(self):
        model = ResultTableModel(None)
        self.assertIsNone(model.get_fetched_at())

    def test_set_data_without_fetched_at_uses_current_time(self):
        model = ResultTableModel(None)
        before = datetime.now()
        model.set_data([])
        after = datetime.now()
        fetched_at = model.get_fetched_at()
        self.assertIsNotNone(fetched_at)
        self.assertTrue(before <= fetched_at <= after)

    def test_set_data_with_explicit_fetched_at_uses_it(self):
        model = ResultTableModel(None)
        explicit_time = datetime(2020, 1, 2, 3, 4, 5)
        model.set_data([], explicit_time)
        self.assertEqual(model.get_fetched_at(), explicit_time)

    def test_clear_resets_fetched_at_to_none(self):
        model = create_model()
        self.assertIsNotNone(model.get_fetched_at())
        model.clear()
        self.assertIsNone(model.get_fetched_at())


if __name__ == "__main__":
    unittest.main()
