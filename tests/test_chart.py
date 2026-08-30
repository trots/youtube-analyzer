import os

if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from datetime import timedelta
from PySide6.QtWidgets import (
    QApplication
)
from youtubeanalyzer.model import (
    ResultTableModel,
    make_result_row
)
from youtubeanalyzer.filters import (
    ResultSortFilterProxyModel
)
from youtubeanalyzer.chart import (
    ChannelsPieChart
)


def create_proxy_model(rows):
    source_model = ResultTableModel(None)
    source_model.set_data(rows)
    proxy_model = ResultSortFilterProxyModel()
    proxy_model.setSourceModel(source_model)
    return proxy_model


class TestChannelsPieChart(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def test_different_channel_link_same_title_creates_two_slices(self):
        rows = [
            make_result_row("Video1", "8 hours ago", "00:34", 1234, "https://video1", "Same Name",
                             "https://channel1", 123, 12345, "2020-05-18", "https://preview1.jpg",
                             "https://logo1.jpg", ["word1"], timedelta(seconds=34), 0, "shorts", []),
            make_result_row("Video2", "9 hours ago", "00:35", 1235, "https://video2", "Same Name",
                             "https://channel2", 124, 12346, "2020-05-19", "https://preview2.jpg",
                             "https://logo2.jpg", ["word2"], timedelta(seconds=35), 1, "shorts", []),
        ]
        proxy_model = create_proxy_model(rows)
        chart = ChannelsPieChart(proxy_model)

        chart.rebuild()

        slices = chart._series.slices()
        self.assertEqual(len(slices), 2)
        for slice in slices:
            self.assertEqual(slice.value(), 1)
            self.assertEqual(slice.label(), "Same Name")

    def test_same_channel_link_aggregates_into_one_slice(self):
        rows = [
            make_result_row("Video1", "8 hours ago", "00:34", 1234, "https://video1", "Channel Name",
                             "https://channel1", 123, 12345, "2020-05-18", "https://preview1.jpg",
                             "https://logo1.jpg", ["word1"], timedelta(seconds=34), 0, "shorts", []),
            make_result_row("Video2", "9 hours ago", "00:35", 1235, "https://video2", "channel name",
                             "https://channel1", 124, 12346, "2020-05-19", "https://preview2.jpg",
                             "https://logo2.jpg", ["word2"], timedelta(seconds=35), 1, "shorts", []),
            make_result_row("Video3", "10 hours ago", "00:36", 1236, "https://video3", "Channel Name",
                             "https://channel1", 125, 12347, "2020-05-20", "https://preview3.jpg",
                             "https://logo3.jpg", ["word3"], timedelta(seconds=36), 2, "shorts", []),
        ]
        proxy_model = create_proxy_model(rows)
        chart = ChannelsPieChart(proxy_model)

        chart.rebuild()

        slices = chart._series.slices()
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices[0].value(), 3)
        self.assertEqual(slices[0].label(), "Channel Name")

    def test_set_current_index_highlights_slice_by_channel_link_not_title(self):
        rows = [
            make_result_row("Video1", "8 hours ago", "00:34", 1234, "https://video1", "Same Name",
                             "https://channel1", 123, 12345, "2020-05-18", "https://preview1.jpg",
                             "https://logo1.jpg", ["word1"], timedelta(seconds=34), 0, "shorts", []),
            make_result_row("Video2", "9 hours ago", "00:35", 1235, "https://video2", "Same Name",
                             "https://channel2", 124, 12346, "2020-05-19", "https://preview2.jpg",
                             "https://logo2.jpg", ["word2"], timedelta(seconds=35), 1, "shorts", []),
        ]
        proxy_model = create_proxy_model(rows)
        chart = ChannelsPieChart(proxy_model)
        chart.rebuild()

        index = proxy_model.index(1, 0)
        chart.set_current_index(index)

        target_slice = chart._slices_by_channel_link["https://channel2"]
        other_slice = chart._slices_by_channel_link["https://channel1"]
        self.assertTrue(target_slice.isExploded())
        self.assertFalse(other_slice.isExploded())

    def test_single_channel_aggregation_and_highlight_regression(self):
        rows = [
            make_result_row("Video1", "8 hours ago", "00:34", 1234, "https://video1", "Channel1",
                             "https://channel1", 123, 12345, "2020-05-18", "https://preview1.jpg",
                             "https://logo1.jpg", ["word1"], timedelta(seconds=34), 0, "shorts", []),
            make_result_row("Video2", "9 hours ago", "00:35", 1235, "https://video2", "Channel1",
                             "https://channel1", 124, 12346, "2020-05-19", "https://preview2.jpg",
                             "https://logo2.jpg", ["word2"], timedelta(seconds=35), 1, "shorts", []),
            make_result_row("Video3", "10 hours ago", "00:36", 1236, "https://video3", "Channel2",
                             "https://channel2", 125, 12347, "2020-05-20", "https://preview3.jpg",
                             "https://logo3.jpg", ["word3"], timedelta(seconds=36), 2, "shorts", []),
        ]
        proxy_model = create_proxy_model(rows)
        chart = ChannelsPieChart(proxy_model)
        chart.rebuild()

        slices = chart._series.slices()
        self.assertEqual(len(slices), 2)

        values_by_label = {s.label(): s.value() for s in slices}
        self.assertEqual(values_by_label["Channel1"], 2)
        self.assertEqual(values_by_label["Channel2"], 1)

        index = proxy_model.index(0, 0)
        chart.set_current_index(index)
        channel1_slice = chart._slices_by_channel_link["https://channel1"]
        channel2_slice = chart._slices_by_channel_link["https://channel2"]
        self.assertTrue(channel1_slice.isExploded())
        self.assertFalse(channel2_slice.isExploded())

        # Hovering the already-highlighted slice must not toggle its label visibility.
        chart._on_slice_hovered(channel1_slice, True)
        self.assertTrue(channel1_slice.isExploded())

        # Hovering another slice must toggle its label visibility as usual.
        chart._on_slice_hovered(channel2_slice, True)
        self.assertTrue(channel2_slice.isLabelVisible())


if __name__ == "__main__":
    unittest.main()
