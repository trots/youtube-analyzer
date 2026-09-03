import os

if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from datetime import timedelta
from unittest.mock import patch
from PySide6.QtCore import Qt, QModelIndex
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
from youtubeanalyzer.filters import (
    AbstractFilter
)
from youtubeanalyzer.export import (
    build_csv_text,
    build_txt_text
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


class _RejectAllFilter(AbstractFilter):
    def filter_accepts_row(self, source_row, source_parent):
        return False


def make_rows(count=1):
    rows = []
    for i in range(count):
        rows.append(make_result_row(
            f"Video{i}", "8 hours ago", "00:34", 1234, f"https://video{i}", f"Channel{i}",
            f"https://channel{i}", 123, 12345, "2020-05-18", "https://preview.jpg",
            "https://logo.jpg", ["word1"], timedelta(seconds=34), i, "shorts", []))
    return rows


class TestExportPanel(unittest.TestCase):

    # Maps each format's combo box label to the SettingsKey quadruple used to persist its settings,
    # mirroring ExportPanel._FORMAT_SETTINGS_KEYS, for tests that check per-format independence directly
    # against QSettings.
    _FORMAT_KEYS = {
        "XLSX": (Settings.ExportFollowTableFiltersXlsx, Settings.ExportSelectedColumnsXlsx,
                 Settings.ExportColumnOrderXlsx, Settings.ExportIncludeHeaderXlsx),
        "CSV": (Settings.ExportFollowTableFiltersCsv, Settings.ExportSelectedColumnsCsv,
                Settings.ExportColumnOrderCsv, Settings.ExportIncludeHeaderCsv),
        "HTML": (Settings.ExportFollowTableFiltersHtml, Settings.ExportSelectedColumnsHtml,
                 Settings.ExportColumnOrderHtml, Settings.ExportIncludeHeaderHtml),
        "TXT": (Settings.ExportFollowTableFiltersTxt, Settings.ExportSelectedColumnsTxt,
                Settings.ExportColumnOrderTxt, Settings.ExportIncludeHeaderTxt),
    }

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._settings_file = "test_video_table_workspace_settings.ini"
        if os.path.isfile(self._settings_file):
            os.remove(self._settings_file)
        self._settings = Settings("test", self._settings_file)
        self._settings._impl.clear()  # QSettings caches values in-process across instances for the same file
        self._workspace = _StubVideoTableWorkspace(self._settings)

    def tearDown(self):
        self._workspace.deleteLater()
        # deleteLater() only schedules destruction; without pumping the event loop the underlying
        # C++ objects survive until some later test happens to process events, and freed memory can
        # get reused by newly-created Qt objects in the meantime (same PySide/shiboken object-identity
        # hazard already noted in PreviewActionsMenu._rebuild_submenus).
        QApplication.processEvents()
        if os.path.isfile(self._settings_file):
            os.remove(self._settings_file)

    def _export_button(self):
        for button in self._workspace._export_panel.findChildren(QPushButton):
            if button.text() == "Export...":
                return button
        raise AssertionError("Export button not found")

    def _copy_to_clipboard_button(self):
        for button in self._workspace._export_panel.findChildren(QPushButton):
            if button.text() == "Copy to Clipboard":
                return button
        raise AssertionError("Copy to Clipboard button not found")

    def _select_format(self, format_text):
        self._select_format_on(self._workspace._export_panel, format_text)

    def _select_format_on(self, export_panel, format_text):
        export_panel._format_combo.setCurrentText(format_text)

    def _set_follow_table_filters(self, checked: bool):
        self._workspace._export_panel._follow_table_filters_checkbox.setChecked(checked)

    def _all_columns(self):
        return list(self._workspace._export_panel._exportable_columns)

    def _column_ids(self, export_panel):
        column_list = export_panel._column_list
        return [column_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(column_list.count())]

    def _column_checked_states(self, export_panel):
        column_list = export_panel._column_list
        return [column_list.item(i).checkState() == Qt.CheckState.Checked for i in range(column_list.count())]

    def _set_column_checked(self, export_panel, index, checked):
        item = export_panel._column_list.item(index)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _move_column(self, export_panel, from_index, to_index):
        column_list = export_panel._column_list
        item = column_list.takeItem(from_index)
        column_list.insertItem(to_index, item)

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

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace.model, self._all_columns(),
                                             include_header=True)

    def test_export_to_csv_button_calls_export_to_csv_with_model(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("CSV")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.csv", "")), \
             patch("youtubeanalyzer.export_panel.export_to_csv") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.csv", self._workspace.model, self._all_columns(),
                                             include_header=True)

    def test_export_to_html_button_calls_export_to_html_with_model(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("HTML")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.html", "")), \
             patch("youtubeanalyzer.export_panel.export_to_html") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.html", self._workspace.model, self._all_columns(),
                                             include_header=True)

    def test_export_to_txt_button_calls_export_to_txt_with_model(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("TXT")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.txt", "")), \
             patch("youtubeanalyzer.export_panel.export_to_txt") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.txt", self._workspace.model, self._all_columns(),
                                             delimiter=" ", include_header=True)

    def test_export_cancelled_dialog_does_not_call_export(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_not_called()

    def test_export_saves_last_save_dir_setting(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("some_dir/out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx"):
            self._export_button().click()

        self.assertTrue(self._settings.get(Settings.LastSaveDir).endswith("some_dir"))

    def test_follow_table_filters_checkbox_unchecked_by_default(self):
        self.assertFalse(self._settings.get(Settings.ExportFollowTableFiltersXlsx))
        self.assertFalse(self._workspace._export_panel._follow_table_filters_checkbox.isChecked())

    def test_follow_table_filters_checkbox_restored_from_settings(self):
        self._settings.set(Settings.ExportFollowTableFiltersXlsx, True)
        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            self.assertTrue(workspace._export_panel._follow_table_filters_checkbox.isChecked())
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_checking_follow_table_filters_checkbox_saves_setting(self):
        self._set_follow_table_filters(True)
        self.assertTrue(self._settings.get(Settings.ExportFollowTableFiltersXlsx))

        self._set_follow_table_filters(False)
        self.assertFalse(self._settings.get(Settings.ExportFollowTableFiltersXlsx))

    def test_export_uses_sort_model_when_follow_table_filters_checked(self):
        self._workspace.model.set_data(make_rows(2))
        self._select_format("XLSX")
        self._set_follow_table_filters(True)

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace._sort_model, self._all_columns(),
                                             include_header=True)

    def test_export_shows_warning_and_skips_dialog_when_filtered_result_is_empty(self):
        self._workspace.model.set_data(make_rows(2))
        self._workspace._sort_model.add_filter(_RejectAllFilter())
        self.assertEqual(self._workspace._sort_model.rowCount(), 0)
        self._select_format("XLSX")
        self._set_follow_table_filters(True)

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName") as mock_dialog, \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export, \
             patch("youtubeanalyzer.export_panel.warning_message") as mock_warning:
            self._export_button().click()

        mock_warning.assert_called_once()
        mock_dialog.assert_not_called()
        mock_export.assert_not_called()

    def test_all_column_checkboxes_checked_by_default(self):
        export_panel = self._workspace._export_panel
        self.assertEqual(export_panel._column_list.count(), len(self._all_columns()))
        self.assertTrue(all(self._column_checked_states(export_panel)))
        self.assertEqual(self._column_ids(export_panel), self._all_columns())

    def test_column_selection_restored_from_settings(self):
        export_panel = self._workspace._export_panel
        original_order = self._column_ids(export_panel)
        self._set_column_checked(export_panel, 0, False)
        self._set_column_checked(export_panel, 1, False)

        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            restored_panel = workspace._export_panel
            checked_states = self._column_checked_states(restored_panel)
            self.assertFalse(checked_states[0])
            self.assertFalse(checked_states[1])
            for checked in checked_states[2:]:
                self.assertTrue(checked)
            # Unchecking columns must not move them in the list, neither immediately nor after the
            # panel (and thus the underlying settings-backed order) is recreated.
            self.assertEqual(self._column_ids(restored_panel), original_order)
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_unchecking_column_does_not_change_its_position(self):
        export_panel = self._workspace._export_panel
        original_order = self._column_ids(export_panel)

        self._set_column_checked(export_panel, 0, False)

        self.assertEqual(self._column_ids(export_panel), original_order)
        self.assertIsNone(self._settings.get(Settings.ExportColumnOrderXlsx))

    def test_toggling_column_checkbox_saves_setting(self):
        export_panel = self._workspace._export_panel
        self._set_column_checked(export_panel, 0, False)

        stored = self._settings.get(Settings.ExportSelectedColumnsXlsx)
        selected_columns = set(int(column) for column in stored.split(","))
        self.assertNotIn(export_panel._exportable_columns[0], selected_columns)
        for column in export_panel._exportable_columns[1:]:
            self.assertIn(column, selected_columns)

    def test_select_none_unchecks_all_columns(self):
        self._workspace.model.set_data(make_rows(1))  # ExportPanel (and its buttons) is disabled at 0 rows
        export_panel = self._workspace._export_panel

        export_panel._select_none_columns_button.click()

        self.assertTrue(all(not checked for checked in self._column_checked_states(export_panel)))
        self.assertEqual(self._settings.get(Settings.ExportSelectedColumnsXlsx), "")

    def test_select_all_checks_all_columns(self):
        self._workspace.model.set_data(make_rows(1))  # ExportPanel (and its buttons) is disabled at 0 rows
        export_panel = self._workspace._export_panel
        export_panel._select_none_columns_button.click()

        export_panel._select_all_columns_button.click()

        self.assertTrue(all(self._column_checked_states(export_panel)))
        stored = self._settings.get(Settings.ExportSelectedColumnsXlsx)
        self.assertEqual(set(int(column) for column in stored.split(",")), set(self._all_columns()))

    def test_select_all_and_select_none_do_not_change_column_order(self):
        self._workspace.model.set_data(make_rows(1))  # ExportPanel (and its buttons) is disabled at 0 rows
        export_panel = self._workspace._export_panel
        self._move_column(export_panel, 0, len(self._all_columns()) - 1)
        expected_order = self._column_ids(export_panel)

        export_panel._select_none_columns_button.click()
        self.assertEqual(self._column_ids(export_panel), expected_order)

        export_panel._select_all_columns_button.click()
        self.assertEqual(self._column_ids(export_panel), expected_order)

    def test_export_with_partial_columns_selected_calls_export_func_with_subset(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")
        export_panel = self._workspace._export_panel
        self._set_column_checked(export_panel, 0, False)
        expected_columns = self._all_columns()[1:]

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace.model, expected_columns,
                                             include_header=True)

    def test_export_with_no_columns_selected_shows_warning_and_skips_export(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")
        export_panel = self._workspace._export_panel
        export_panel._select_none_columns_button.click()

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName") as mock_dialog, \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export, \
             patch("youtubeanalyzer.export_panel.warning_message") as mock_warning:
            self._export_button().click()

        mock_warning.assert_called_once()
        mock_dialog.assert_not_called()
        mock_export.assert_not_called()

    def test_column_list_built_in_saved_order_with_new_column_appended(self):
        # Simulate a previously-saved order that differs from canonical order and omits one column,
        # together with an independently-saved selection.
        all_columns = self._all_columns()
        saved_order = list(reversed(all_columns[1:]))
        self._settings.set(Settings.ExportColumnOrderXlsx, ",".join(str(c) for c in saved_order))
        saved_selection = saved_order[:-1]  # all but the last of the saved-order columns are checked
        self._settings.set(Settings.ExportSelectedColumnsXlsx, ",".join(str(c) for c in saved_selection))

        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            export_panel = workspace._export_panel
            # The new column (all_columns[0]), absent from the saved order, is appended at the end.
            expected_order = saved_order + [all_columns[0]]
            self.assertEqual(self._column_ids(export_panel), expected_order)
            checked_states = self._column_checked_states(export_panel)
            expected_checked = [column in saved_selection for column in expected_order]
            self.assertEqual(checked_states, expected_checked)
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_reordering_columns_saves_new_order_to_settings(self):
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()

        self._move_column(export_panel, 0, len(all_columns) - 1)
        export_panel._save_column_order()

        expected_order = all_columns[1:] + [all_columns[0]]
        stored = self._settings.get(Settings.ExportColumnOrderXlsx)
        self.assertEqual([int(c) for c in stored.split(",")], expected_order)
        # Reordering must not touch the independently-persisted selection.
        self.assertIsNone(self._settings.get(Settings.ExportSelectedColumnsXlsx))

    def test_reordering_columns_persists_across_panel_recreation(self):
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()
        self._move_column(export_panel, 0, len(all_columns) - 1)
        export_panel._save_column_order()
        expected_order = all_columns[1:] + [all_columns[0]]

        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            self.assertEqual(self._column_ids(workspace._export_panel), expected_order)
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_drag_and_drop_move_triggers_save_via_rows_moved_signal(self):
        # Emulates the actual drag & drop mechanism (QAbstractItemModel.moveRow), rather than calling
        # _save_column_order() directly, to exercise the rowsMoved wiring itself.
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()

        list_model = export_panel._column_list.model()
        list_model.moveRow(QModelIndex(), 0, QModelIndex(), len(all_columns))

        expected_order = all_columns[1:] + [all_columns[0]]
        self.assertEqual(self._column_ids(export_panel), expected_order)
        stored = self._settings.get(Settings.ExportColumnOrderXlsx)
        self.assertEqual([int(c) for c in stored.split(",")], expected_order)
        # Moving a column must not touch the independently-persisted selection.
        self.assertIsNone(self._settings.get(Settings.ExportSelectedColumnsXlsx))

    def test_export_uses_columns_in_list_order_not_canonical_order(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()
        self._move_column(export_panel, 0, len(all_columns) - 1)
        expected_order = all_columns[1:] + [all_columns[0]]

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace.model, expected_order,
                                             include_header=True)

    def test_include_header_checkbox_checked_by_default(self):
        self.assertTrue(self._settings.get(Settings.ExportIncludeHeaderXlsx))
        self.assertTrue(self._workspace._export_panel._include_header_checkbox.isChecked())

    def test_include_header_checkbox_restored_from_settings(self):
        self._settings.set(Settings.ExportIncludeHeaderXlsx, False)
        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            self.assertFalse(workspace._export_panel._include_header_checkbox.isChecked())
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_unchecking_include_header_checkbox_saves_setting(self):
        self._workspace._export_panel._include_header_checkbox.setChecked(False)
        self.assertFalse(self._settings.get(Settings.ExportIncludeHeaderXlsx))

        self._workspace._export_panel._include_header_checkbox.setChecked(True)
        self.assertTrue(self._settings.get(Settings.ExportIncludeHeaderXlsx))

    def test_unchecking_include_header_checkbox_is_passed_to_export_func(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("XLSX")
        self._workspace._export_panel._include_header_checkbox.setChecked(False)

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace.model, self._all_columns(),
                                             include_header=False)

    def test_txt_delimiter_default_from_settings(self):
        self.assertEqual(self._settings.get(Settings.ExportDelimiterTxt), " ")
        self.assertEqual(self._workspace._export_panel._txt_delimiter_edit.text(), " ")

    def test_txt_delimiter_restored_from_settings(self):
        self._settings.set(Settings.ExportDelimiterTxt, "|")
        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            self.assertEqual(workspace._export_panel._txt_delimiter_edit.text(), "|")
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_changing_txt_delimiter_saves_setting(self):
        self._workspace._export_panel._txt_delimiter_edit.setText("|")
        self.assertEqual(self._settings.get(Settings.ExportDelimiterTxt), "|")

    def test_txt_delimiter_is_passed_to_export_to_txt(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("TXT")
        self._workspace._export_panel._txt_delimiter_edit.setText("|")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.txt", "")), \
             patch("youtubeanalyzer.export_panel.export_to_txt") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.txt", self._workspace.model, self._all_columns(),
                                             delimiter="|", include_header=True)

    def test_txt_delimiter_not_passed_to_non_txt_export_funcs(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("CSV")
        self._workspace._export_panel._txt_delimiter_edit.setText("|")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.csv", "")), \
             patch("youtubeanalyzer.export_panel.export_to_csv") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.csv", self._workspace.model, self._all_columns(),
                                             include_header=True)

    def test_all_four_formats_start_with_default_values(self):
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()
        for format_label in ("XLSX", "CSV", "HTML", "TXT"):
            self._select_format(format_label)
            self.assertEqual(self._column_ids(export_panel), all_columns)
            self.assertTrue(all(self._column_checked_states(export_panel)))
            self.assertTrue(export_panel._include_header_checkbox.isChecked())
            self.assertFalse(export_panel._follow_table_filters_checkbox.isChecked())

    def test_switching_format_restores_saved_column_selection_and_order(self):
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()

        # XLSX (the default format): uncheck the first column and move the second column to the end.
        self._set_column_checked(export_panel, 0, False)
        self._move_column(export_panel, 1, len(all_columns) - 1)
        export_panel._save_column_order()
        xlsx_order = self._column_ids(export_panel)
        xlsx_checked = self._column_checked_states(export_panel)

        # CSV starts from its own defaults, independent of the XLSX changes above.
        self._select_format("CSV")
        self.assertEqual(self._column_ids(export_panel), all_columns)
        self.assertTrue(all(self._column_checked_states(export_panel)))
        self._set_column_checked(export_panel, 2, False)
        csv_checked = self._column_checked_states(export_panel)

        # Switching back to XLSX restores exactly the order/selection saved for XLSX.
        self._select_format("XLSX")
        self.assertEqual(self._column_ids(export_panel), xlsx_order)
        self.assertEqual(self._column_checked_states(export_panel), xlsx_checked)

        # Switching to CSV again restores exactly the selection saved for CSV.
        self._select_format("CSV")
        self.assertEqual(self._column_ids(export_panel), all_columns)
        self.assertEqual(self._column_checked_states(export_panel), csv_checked)

    def test_switching_format_restores_saved_checkboxes(self):
        export_panel = self._workspace._export_panel

        self._set_follow_table_filters(True)
        export_panel._include_header_checkbox.setChecked(False)

        self._select_format("CSV")
        self.assertFalse(export_panel._follow_table_filters_checkbox.isChecked())
        self.assertTrue(export_panel._include_header_checkbox.isChecked())

        export_panel._follow_table_filters_checkbox.setChecked(True)
        export_panel._include_header_checkbox.setChecked(False)

        self._select_format("XLSX")
        self.assertTrue(export_panel._follow_table_filters_checkbox.isChecked())
        self.assertFalse(export_panel._include_header_checkbox.isChecked())

        self._select_format("CSV")
        self.assertTrue(export_panel._follow_table_filters_checkbox.isChecked())
        self.assertFalse(export_panel._include_header_checkbox.isChecked())

    def test_configuring_one_format_does_not_change_settings_of_other_formats(self):
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()

        # Configure XLSX (the default format) only.
        self._set_column_checked(export_panel, 0, False)
        self._move_column(export_panel, 1, len(all_columns) - 1)
        export_panel._save_column_order()
        self._set_follow_table_filters(True)
        export_panel._include_header_checkbox.setChecked(False)

        for format_label in ("CSV", "HTML", "TXT"):
            follow_key, selected_key, order_key, header_key = self._FORMAT_KEYS[format_label]
            self.assertFalse(self._settings.get(follow_key))
            self.assertIsNone(self._settings.get(selected_key))
            self.assertIsNone(self._settings.get(order_key))
            self.assertTrue(self._settings.get(header_key))

    def test_select_all_and_select_none_only_affect_current_format(self):
        self._workspace.model.set_data(make_rows(1))  # ExportPanel (and its buttons) is disabled at 0 rows
        export_panel = self._workspace._export_panel

        export_panel._select_none_columns_button.click()  # Affects XLSX (the default format) only.

        self._select_format("CSV")
        self.assertTrue(all(self._column_checked_states(export_panel)))
        self.assertIsNone(self._settings.get(Settings.ExportSelectedColumnsCsv))

        self._select_format("XLSX")
        self.assertTrue(all(not checked for checked in self._column_checked_states(export_panel)))

    def test_per_format_settings_persist_across_workspace_recreation(self):
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()

        self._select_format("XLSX")
        self._set_column_checked(export_panel, 0, False)
        self._set_follow_table_filters(True)

        self._select_format("CSV")
        self._set_column_checked(export_panel, 1, False)
        export_panel._include_header_checkbox.setChecked(False)

        self._select_format("HTML")
        self._move_column(export_panel, 0, len(all_columns) - 1)
        export_panel._save_column_order()
        html_order = all_columns[1:] + [all_columns[0]]

        self._select_format("TXT")
        self._set_follow_table_filters(True)
        export_panel._include_header_checkbox.setChecked(False)

        workspace = _StubVideoTableWorkspace(self._settings)
        try:
            restored_panel = workspace._export_panel

            self._select_format_on(restored_panel, "XLSX")
            self.assertFalse(self._column_checked_states(restored_panel)[0])
            self.assertTrue(restored_panel._follow_table_filters_checkbox.isChecked())

            self._select_format_on(restored_panel, "CSV")
            self.assertFalse(self._column_checked_states(restored_panel)[1])
            self.assertFalse(restored_panel._include_header_checkbox.isChecked())

            self._select_format_on(restored_panel, "HTML")
            self.assertEqual(self._column_ids(restored_panel), html_order)

            self._select_format_on(restored_panel, "TXT")
            self.assertTrue(restored_panel._follow_table_filters_checkbox.isChecked())
            self.assertFalse(restored_panel._include_header_checkbox.isChecked())
        finally:
            workspace.deleteLater()
            QApplication.processEvents()

    def test_export_uses_columns_and_checkboxes_saved_for_selected_format(self):
        self._workspace.model.set_data(make_rows(1))
        export_panel = self._workspace._export_panel
        all_columns = self._all_columns()

        # Configure XLSX with a partial column selection and no header row.
        self._select_format("XLSX")
        self._set_column_checked(export_panel, 0, False)
        export_panel._include_header_checkbox.setChecked(False)
        xlsx_columns = all_columns[1:]

        # Configure CSV differently: all columns (default), follow table filters on.
        self._select_format("CSV")
        self._set_follow_table_filters(True)

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.csv", "")), \
             patch("youtubeanalyzer.export_panel.export_to_csv") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.csv", self._workspace._sort_model, all_columns,
                                             include_header=True)

        # Switching back to XLSX and exporting must use XLSX's own saved settings, not CSV's.
        self._select_format("XLSX")
        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName",
                   return_value=("out.xlsx", "")), \
             patch("youtubeanalyzer.export_panel.export_to_xlsx") as mock_export:
            self._export_button().click()

        mock_export.assert_called_once_with("out.xlsx", self._workspace.model, xlsx_columns,
                                             include_header=False)

    def test_copy_to_clipboard_button_visible_only_for_csv_and_txt(self):
        button = self._copy_to_clipboard_button()

        self._select_format("XLSX")
        self.assertTrue(button.isHidden())

        self._select_format("CSV")
        self.assertFalse(button.isHidden())

        self._select_format("HTML")
        self.assertTrue(button.isHidden())

        self._select_format("TXT")
        self.assertFalse(button.isHidden())

    def test_copy_to_clipboard_for_csv_copies_same_text_export_would_write(self):
        self._workspace.model.set_data(make_rows(2))
        self._select_format("CSV")
        expected_text = build_csv_text(self._workspace.model, self._all_columns(), include_header=True)

        with patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard") as mock_clipboard:
            self._copy_to_clipboard_button().click()

        mock_clipboard.return_value.setText.assert_called_once_with(expected_text)

    def test_copy_to_clipboard_for_txt_copies_same_text_export_would_write(self):
        self._workspace.model.set_data(make_rows(2))
        self._select_format("TXT")
        self._workspace._export_panel._txt_delimiter_edit.setText("|")
        expected_text = build_txt_text(self._workspace.model, self._all_columns(), delimiter="|", include_header=True)

        with patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard") as mock_clipboard:
            self._copy_to_clipboard_button().click()

        mock_clipboard.return_value.setText.assert_called_once_with(expected_text)

    def test_copy_to_clipboard_uses_sort_model_when_follow_table_filters_checked(self):
        self._workspace.model.set_data(make_rows(2))
        self._select_format("CSV")
        self._set_follow_table_filters(True)
        expected_text = build_csv_text(self._workspace._sort_model, self._all_columns(), include_header=True)

        with patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard") as mock_clipboard:
            self._copy_to_clipboard_button().click()

        mock_clipboard.return_value.setText.assert_called_once_with(expected_text)

    def test_copy_to_clipboard_respects_selected_columns_order_and_header_setting(self):
        self._workspace.model.set_data(make_rows(2))
        self._select_format("CSV")
        export_panel = self._workspace._export_panel
        self._move_column(export_panel, 0, len(self._all_columns()) - 1)
        expected_columns = self._all_columns()[1:] + [self._all_columns()[0]]
        export_panel._include_header_checkbox.setChecked(False)
        expected_text = build_csv_text(self._workspace.model, expected_columns, include_header=False)

        with patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard") as mock_clipboard:
            self._copy_to_clipboard_button().click()

        mock_clipboard.return_value.setText.assert_called_once_with(expected_text)

    def test_copy_to_clipboard_shows_warning_and_does_not_touch_clipboard_when_filtered_result_is_empty(self):
        self._workspace.model.set_data(make_rows(2))
        self._workspace._sort_model.add_filter(_RejectAllFilter())
        self.assertEqual(self._workspace._sort_model.rowCount(), 0)
        self._select_format("CSV")
        self._set_follow_table_filters(True)

        with patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard") as mock_clipboard, \
             patch("youtubeanalyzer.export_panel.warning_message") as mock_warning:
            self._copy_to_clipboard_button().click()

        mock_warning.assert_called_once()
        mock_clipboard.return_value.setText.assert_not_called()

    def test_copy_to_clipboard_shows_warning_and_does_not_touch_clipboard_when_no_columns_selected(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("CSV")
        export_panel = self._workspace._export_panel
        export_panel._select_none_columns_button.click()

        with patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard") as mock_clipboard, \
             patch("youtubeanalyzer.export_panel.warning_message") as mock_warning:
            self._copy_to_clipboard_button().click()

        mock_warning.assert_called_once()
        mock_clipboard.return_value.setText.assert_not_called()

    def test_copy_to_clipboard_does_not_open_save_dialog_or_touch_last_save_dir(self):
        self._workspace.model.set_data(make_rows(1))
        self._select_format("CSV")

        with patch("youtubeanalyzer.export_panel.QFileDialog.getSaveFileName") as mock_dialog, \
             patch("youtubeanalyzer.export_panel.QGuiApplication.clipboard"):
            self._copy_to_clipboard_button().click()

        mock_dialog.assert_not_called()
        self.assertEqual(self._settings.get(Settings.LastSaveDir), "")


if __name__ == "__main__":
    unittest.main()
