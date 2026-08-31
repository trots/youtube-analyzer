import os

if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from datetime import timedelta
from unittest.mock import patch
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.model import (
    make_result_row
)
from youtubeanalyzer.video_table_workspace import (
    AbstractVideoTableWorkspace
)


class _StubVideoTableWorkspace(AbstractVideoTableWorkspace):
    """A minimal concrete AbstractVideoTableWorkspace subclass for testing the base class behavior."""

    def get_data_name(self):
        return "test_data"

    def _create_toolbar(self, h_layout: QHBoxLayout):
        pass

    def _on_search_clicked(self):
        pass


def make_rows(count=1):
    rows = []
    for i in range(count):
        rows.append(make_result_row(
            f"Video{i}", "8 hours ago", "00:34", 1234, f"https://video{i}", f"Channel{i}",
            f"https://channel{i}", 123, 12345, "2020-05-18", "https://preview.jpg",
            "https://logo.jpg", ["word1"], timedelta(seconds=34), i, "shorts", []))
    return rows


class TestExportPanel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._settings_file = "test_video_table_workspace_settings.ini"
        if os.path.isfile(self._settings_file):
            os.remove(self._settings_file)
        self._settings = Settings("test", self._settings_file)
        self._workspace = _StubVideoTableWorkspace(self._settings)

    def tearDown(self):
        self._workspace.deleteLater()
        if os.path.isfile(self._settings_file):
            os.remove(self._settings_file)

    def _export_button(self):
        return self._workspace._export_panel.findChildren(QPushButton)[0]

    def _select_format(self, format_text):
        self._workspace._export_panel._format_combo.setCurrentText(format_text)

    def test_export_tab_present_after_analytics_tab(self):
        side_tab_widget = self._workspace._side_tab_widget
        self.assertEqual(side_tab_widget.count(), 3)
        self.assertEqual(side_tab_widget.tabText(0), "Details")
        self.assertEqual(side_tab_widget.tabText(1), "Analytics")
        self.assertEqual(side_tab_widget.tabText(2), "Export")
        self.assertIs(side_tab_widget.widget(2), self._workspace._export_panel)

    def test_export_tab_is_reachable_by_direct_switch(self):
        side_tab_widget = self._workspace._side_tab_widget
        side_tab_widget.setCurrentIndex(0)
        side_tab_widget.setCurrentIndex(2)
        self.assertEqual(side_tab_widget.currentIndex(), 2)

    def test_show_export_tab_switches_side_panel_to_export(self):
        side_tab_widget = self._workspace._side_tab_widget
        side_tab_widget.setCurrentIndex(0)

        self._workspace.show_export_tab()

        self.assertEqual(side_tab_widget.currentIndex(), 2)
        self.assertIs(side_tab_widget.currentWidget(), self._workspace._export_panel)

    def test_export_panel_disabled_when_model_is_empty(self):
        self.assertEqual(self._workspace.model.rowCount(), 0)
        self.assertFalse(self._workspace._export_panel.isEnabled())

    def test_export_panel_enabled_after_rows_added_and_disabled_after_cleared(self):
        export_panel = self._workspace._export_panel

        self._workspace.model.set_data(make_rows(2))
        self.assertTrue(export_panel.isEnabled())

        self._workspace.model.clear()
        self.assertFalse(export_panel.isEnabled())

    def test_export_to_xlsx_button_calls_export_to_xlsx_with_model(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")

        with patch("youtubeanalyzer.video_table_workspace.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.video_table_workspace.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace.model)

    def test_export_to_csv_button_calls_export_to_csv_with_model(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("CSV")

        with patch("youtubeanalyzer.video_table_workspace.QFileDialog.getSaveFileName",
                   return_value=("out.csv", "")), \
             patch("youtubeanalyzer.video_table_workspace.export_to_csv") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.csv", self._workspace.model)

    def test_export_to_html_button_calls_export_to_html_with_model(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("HTML")

        with patch("youtubeanalyzer.video_table_workspace.QFileDialog.getSaveFileName",
                   return_value=("out.html", "")), \
             patch("youtubeanalyzer.video_table_workspace.export_to_html") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.html", self._workspace.model)

    def test_export_cancelled_dialog_does_not_call_export(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")

        with patch("youtubeanalyzer.video_table_workspace.QFileDialog.getSaveFileName",
                   return_value=("", "")), \
             patch("youtubeanalyzer.video_table_workspace.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_not_called()

    def test_export_saves_last_save_dir_setting(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")

        with patch("youtubeanalyzer.video_table_workspace.QFileDialog.getSaveFileName",
                   return_value=("some_dir/out.xlsx", "")), \
             patch("youtubeanalyzer.video_table_workspace.export_to_xlsx"):
            self._export_button().click()

        self.assertTrue(self._settings.get(Settings.LastSaveDir).endswith("some_dir"))


if __name__ == "__main__":
    unittest.main()
