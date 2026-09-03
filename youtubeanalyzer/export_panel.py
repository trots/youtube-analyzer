from PySide6.QtCore import (
    Qt,
    QFileInfo
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QFileDialog
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.model import (
    ResultTableModel
)
from youtubeanalyzer.filters import (
    ResultSortFilterProxyModel
)
from youtubeanalyzer.widgets import (
    warning_message
)
from youtubeanalyzer.export import (
    export_to_xlsx,
    export_to_csv,
    export_to_html,
    export_to_txt,
    get_exportable_columns
)


class ExportPanel(QWidget):
    # Maps each export format to the SettingsKey quadruple ("follow_table_filters" / "selected_columns" /
    # "column_order" / "include_header") that stores the settings for that format. Used as the single
    # point of "format -> SettingsKey" lookup, instead of scattering per-format branches through the code.
    _FORMAT_SETTINGS_KEYS = {
        "xlsx": {
            "follow_table_filters": Settings.ExportFollowTableFiltersXlsx,
            "selected_columns": Settings.ExportSelectedColumnsXlsx,
            "column_order": Settings.ExportColumnOrderXlsx,
            "include_header": Settings.ExportIncludeHeaderXlsx,
        },
        "csv": {
            "follow_table_filters": Settings.ExportFollowTableFiltersCsv,
            "selected_columns": Settings.ExportSelectedColumnsCsv,
            "column_order": Settings.ExportColumnOrderCsv,
            "include_header": Settings.ExportIncludeHeaderCsv,
        },
        "html": {
            "follow_table_filters": Settings.ExportFollowTableFiltersHtml,
            "selected_columns": Settings.ExportSelectedColumnsHtml,
            "column_order": Settings.ExportColumnOrderHtml,
            "include_header": Settings.ExportIncludeHeaderHtml,
        },
        "txt": {
            "follow_table_filters": Settings.ExportFollowTableFiltersTxt,
            "selected_columns": Settings.ExportSelectedColumnsTxt,
            "column_order": Settings.ExportColumnOrderTxt,
            "include_header": Settings.ExportIncludeHeaderTxt,
        },
    }

    def __init__(self, settings: Settings, model: ResultTableModel, sort_model: ResultSortFilterProxyModel,
                 get_data_name, parent: QWidget = None):
        super().__init__(parent)
        self._settings: Settings = settings
        self._model: ResultTableModel = model
        self._sort_model: ResultSortFilterProxyModel = sort_model
        self._get_data_name = get_data_name

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel(self.tr("Format:")))

        self._format_combo = QComboBox()
        self._format_combo.addItem("XLSX", ("xlsx", self.tr("Save XLSX"), self.tr("Xlsx File (*.xlsx)"), ".xlsx"))
        self._format_combo.addItem("CSV", ("csv", self.tr("Save CSV"), self.tr("Csv File (*.csv)"), ".csv"))
        self._format_combo.addItem("HTML", ("html", self.tr("Save HTML"), self.tr("Html File (*.html)"), ".html"))
        self._format_combo.addItem("TXT", ("txt", self.tr("Save TXT"), self.tr("Text File (*.txt)"), ".txt"))
        main_layout.addWidget(self._format_combo)

        self._follow_table_filters_checkbox = QCheckBox(self.tr("Follow table filters and sort order"))
        self._follow_table_filters_checkbox.setChecked(self._settings.get(self._current_keys()["follow_table_filters"]))
        self._follow_table_filters_checkbox.toggled.connect(self._on_follow_table_filters_toggled)
        main_layout.addWidget(self._follow_table_filters_checkbox)

        self._include_header_checkbox = QCheckBox(self.tr("Include header row"))
        self._include_header_checkbox.setChecked(self._settings.get(self._current_keys()["include_header"]))
        self._include_header_checkbox.toggled.connect(self._on_include_header_toggled)
        main_layout.addWidget(self._include_header_checkbox)

        main_layout.addWidget(QLabel(self.tr("Columns:")))

        columns_buttons_layout = QHBoxLayout()
        self._select_all_columns_button = QPushButton(self.tr("Select All"))
        self._select_all_columns_button.clicked.connect(self._on_select_all_columns_clicked)
        columns_buttons_layout.addWidget(self._select_all_columns_button)
        self._select_none_columns_button = QPushButton(self.tr("Select None"))
        self._select_none_columns_button.clicked.connect(self._on_select_none_columns_clicked)
        columns_buttons_layout.addWidget(self._select_none_columns_button)
        main_layout.addLayout(columns_buttons_layout)

        self._exportable_columns: list[int] = get_exportable_columns()
        self._column_list = QListWidget()
        self._column_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._populate_column_list()
        self._column_list.itemChanged.connect(self._on_column_item_changed)
        self._column_list.model().rowsMoved.connect(self._on_columns_reordered)
        main_layout.addWidget(self._column_list)

        self._txt_delimiter_label = QLabel(self.tr("TXT delimiter:"))
        main_layout.addWidget(self._txt_delimiter_label)
        self._txt_delimiter_edit = QLineEdit(self._settings.get(Settings.ExportDelimiterTxt))
        self._txt_delimiter_edit.textChanged.connect(self._on_txt_delimiter_changed)
        main_layout.addWidget(self._txt_delimiter_edit)

        export_button = QPushButton(self.tr("Export..."))
        export_button.clicked.connect(self._export)
        main_layout.addWidget(export_button)

        main_layout.addStretch()

        self._format_combo.currentIndexChanged.connect(self._update_txt_delimiter_visibility)
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        self._update_txt_delimiter_visibility()

    def _current_format(self) -> str:
        return self._format_combo.currentData()[0]

    def _current_keys(self) -> dict:
        return ExportPanel._FORMAT_SETTINGS_KEYS[self._current_format()]

    def _populate_column_list(self):
        for column, checked in self._build_ordered_columns():
            item = QListWidgetItem(self._model.FieldNames[column])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, column)
            self._column_list.addItem(item)

    def _on_format_changed(self, _index: int):
        keys = self._current_keys()

        self._follow_table_filters_checkbox.blockSignals(True)
        self._follow_table_filters_checkbox.setChecked(self._settings.get(keys["follow_table_filters"]))
        self._follow_table_filters_checkbox.blockSignals(False)

        self._include_header_checkbox.blockSignals(True)
        self._include_header_checkbox.setChecked(self._settings.get(keys["include_header"]))
        self._include_header_checkbox.blockSignals(False)

        self._column_list.blockSignals(True)
        self._column_list.clear()
        self._populate_column_list()
        self._column_list.blockSignals(False)

    def _on_follow_table_filters_toggled(self, checked: bool):
        self._settings.set(self._current_keys()["follow_table_filters"], checked)

    def _on_include_header_toggled(self, checked: bool):
        self._settings.set(self._current_keys()["include_header"], checked)

    def _on_txt_delimiter_changed(self, text: str):
        self._settings.set(Settings.ExportDelimiterTxt, text)

    def _update_txt_delimiter_visibility(self):
        is_txt = self._format_combo.currentData()[0] == "txt"
        self._txt_delimiter_label.setVisible(is_txt)
        self._txt_delimiter_edit.setVisible(is_txt)

    def _build_ordered_columns(self) -> list[tuple[int, bool]]:
        """Returns (column_id, checked) pairs in the order the column list should be built: columns from
        the stored order first (in the stored order), then any remaining exportable columns that were
        not in the stored order (in canonical order) at the end. Checked state is determined separately,
        by membership in the stored set of selected columns."""
        order = self._load_column_order()
        selected = self._load_selected_columns()
        return [(column, column in selected) for column in order]

    def _load_column_order(self) -> list[int]:
        """Returns the order of all exportable columns: columns from the stored setting first (in the
        stored order), then any remaining exportable columns that were not in the stored setting (in
        canonical order)."""
        stored = self._settings.get(self._current_keys()["column_order"])
        if not stored:
            return list(self._exportable_columns)
        saved_order = [int(column) for column in stored.split(",")]

        ordered: list[int] = []
        seen: set[int] = set()
        for column in saved_order:
            if column in self._exportable_columns and column not in seen:
                ordered.append(column)
                seen.add(column)
        for column in self._exportable_columns:
            if column not in seen:
                ordered.append(column)
        return ordered

    def _load_selected_columns(self) -> set[int]:
        """Returns the set of columns that should be checked, based on the "selected_columns" setting of
        the current format: None means all exportable columns are checked, "" means none are checked,
        otherwise the stored comma-separated list of IDs."""
        stored = self._settings.get(self._current_keys()["selected_columns"])
        if stored is None:
            return set(self._exportable_columns)
        if not stored:
            return set()
        return {int(column) for column in stored.split(",")}

    def _selected_columns(self) -> list[int]:
        columns = []
        for i in range(self._column_list.count()):
            item = self._column_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                columns.append(item.data(Qt.ItemDataRole.UserRole))
        return columns

    def _all_columns_in_order(self) -> list[int]:
        return [self._column_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self._column_list.count())]

    def _save_selected_columns(self):
        selected = self._selected_columns()
        self._settings.set(self._current_keys()["selected_columns"], ",".join(str(column) for column in selected))

    def _save_column_order(self):
        order = self._all_columns_in_order()
        self._settings.set(self._current_keys()["column_order"], ",".join(str(column) for column in order))

    def _on_column_item_changed(self, _item: QListWidgetItem):
        self._save_selected_columns()

    def _on_columns_reordered(self, *_args):
        self._save_column_order()

    def _on_select_all_columns_clicked(self):
        self._set_all_columns_checked(True)

    def _on_select_none_columns_clicked(self):
        self._set_all_columns_checked(False)

    def _set_all_columns_checked(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self._column_list.blockSignals(True)
        for i in range(self._column_list.count()):
            self._column_list.item(i).setCheckState(state)
        self._column_list.blockSignals(False)
        self._save_selected_columns()

    def _export(self):
        export_format, caption, filter, file_suffix = self._format_combo.currentData()
        export_func = {"xlsx": export_to_xlsx, "csv": export_to_csv, "html": export_to_html,
                       "txt": export_to_txt}[export_format]
        follow_table_filters = self._follow_table_filters_checkbox.isChecked()
        export_model = self._sort_model if follow_table_filters else self._model
        if follow_table_filters and self._sort_model.rowCount() == 0:
            warning_message(self, self.tr("No rows match the current table filters"))
            return
        selected_columns = self._selected_columns()
        if not selected_columns:
            warning_message(self, self.tr("Select at least one column to export"))
            return
        data_name = self._get_data_name() or "export"
        last_save_dir = self._settings.get(Settings.LastSaveDir)
        file_name, _ = QFileDialog.getSaveFileName(
            self, caption=caption, filter=filter, dir=(last_save_dir + "/" + data_name + file_suffix))
        if not file_name:
            return
        self._settings.set(Settings.LastSaveDir, QFileInfo(file_name).dir().absolutePath())
        include_header = self._include_header_checkbox.isChecked()
        if export_format == "txt":
            export_func(file_name, export_model, selected_columns,
                        delimiter=self._txt_delimiter_edit.text(), include_header=include_header)
        else:
            export_func(file_name, export_model, selected_columns, include_header=include_header)
