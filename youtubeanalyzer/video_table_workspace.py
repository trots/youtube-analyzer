from typing import Optional
import re
from PySide6.QtCore import (
    Signal,
    QSize,
    Qt,
    QEvent,
    QModelIndex,
    QUrl,
    QFileInfo,
    QItemSelection
)
from PySide6.QtGui import (
    QAction,
    QPixmap,
    QPainter,
    QGuiApplication
)
from PySide6.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QTextEdit,
    QStackedLayout,
    QComboBox,
    QCheckBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QSplitter,
    QFrame,
    QButtonGroup,
    QRadioButton,
    QListView,
    QSlider,
    QMenu,
    QToolButton,
    QFileDialog,
    QStyle
)
from PySide6.QtCharts import (
    QChartView,
    QChart
)
from youtubeanalyzer.theme import (
    Theme
)
from youtubeanalyzer.settings import (
    Settings,
    StateSaveable
)
from youtubeanalyzer.engine import (
    ImageDownloader,
    FileDownloader
)
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel
)
from youtubeanalyzer.filters import (
    ResultSortFilterProxyModel,
    FiltersPanel
)
from youtubeanalyzer.chart import (
    ChannelsPieChart,
    VideoDurationChart,
    WordsPieChart
)
from youtubeanalyzer.widgets import (
    create_link_label,
    critical_detailed_message,
    warning_message,
    PixmapLabel,
    FixedTabWidget
)
from youtubeanalyzer.workspace import (
    WorkspaceWidget
)
from youtubeanalyzer.export import (
    export_to_xlsx,
    export_to_csv,
    export_to_html,
    get_exportable_columns
)


class PreviewActionsMenu(QMenu):
    class Actions:
        Copy: int = 1
        Download: int = 2
        All: int = Copy | Download

    def __init__(self, settings: Settings, actions: int = Actions.All, parent: QWidget = None):
        super().__init__(parent)
        self._settings: Settings = settings
        self._video_title: str = ""
        self._preview_sizes: list[dict] = []
        self._pending_downloads: dict[str, str] = {}  # {url: save file path}

        self._download_submenu: Optional[QMenu] = None
        self._download_downloader: Optional[FileDownloader] = None
        if actions & PreviewActionsMenu.Actions.Download:
            self._download_submenu = self.addMenu(self.tr("Download preview"))
            self._download_downloader = FileDownloader(self)
            self._download_downloader.finished.connect(self._on_file_downloaded)
            self._download_downloader.error.connect(self._on_download_error)

        self._copy_submenu: Optional[QMenu] = None
        self._copy_downloader: Optional[ImageDownloader] = None
        if actions & PreviewActionsMenu.Actions.Copy:
            self._copy_submenu = self.addMenu(self.tr("Copy preview"))
            self._copy_downloader = ImageDownloader(self)
            self._copy_downloader.finished.connect(self._on_image_downloaded)
            self._copy_downloader.error.connect(self._on_copy_error)

    def set_current_video(self, video_title: str, preview_sizes: list[dict]):
        self._video_title = video_title
        self._preview_sizes = preview_sizes or []
        self._rebuild_submenus()

    def has_sizes(self) -> bool:
        return bool(self._preview_sizes)

    def _rebuild_submenus(self):
        # Reuse existing QAction objects instead of clear()+addAction() on every call: tearing down and
        # recreating Qt objects on every row selection was hitting a rare PySide/shiboken object-identity
        # bug when colliding with QNetworkReply objects freed around the same time (deleteLater()).
        if self._download_submenu is not None:
            self._sync_submenu_actions(self._download_submenu, self._download)
        if self._copy_submenu is not None:
            self._sync_submenu_actions(self._copy_submenu, self._copy)

    def _sync_submenu_actions(self, submenu: QMenu, on_size_selected) -> None:
        actions = submenu.actions()
        for i, size in enumerate(self._preview_sizes):
            label = f"{size['width']}×{size['height']}"
            if i < len(actions):
                action = actions[i]
                action.setText(label)
                action.setVisible(True)
                action.triggered.disconnect()
            else:
                action = submenu.addAction(label)
            action.triggered.connect(lambda checked=False, s=size: on_size_selected(s))
        for extra_action in actions[len(self._preview_sizes):]:
            extra_action.setVisible(False)

    def _download(self, size: dict):
        url = size["url"]
        extension = QUrl(url).path().rsplit(".", 1)[-1] if "." in QUrl(url).path() else "jpg"
        default_name = self._sanitize_filename(self._video_title) + "." + extension
        last_save_dir = self._settings.get(Settings.LastPreviewSaveDir)
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save preview image"), last_save_dir + "/" + default_name,
            self.tr("Images") + f" (*.{extension})")
        if not file_path:
            return
        self._settings.set(Settings.LastPreviewSaveDir, QFileInfo(file_path).dir().absolutePath())

        request_url = QUrl(url)
        self._pending_downloads[request_url.toString()] = file_path
        self._download_downloader.start_download(request_url)

    def _on_file_downloaded(self, url: QUrl, data: bytes):
        file_path = self._pending_downloads.pop(url.toString(), None)
        if file_path is None:
            return
        try:
            with open(file_path, "wb") as preview_file:
                preview_file.write(data)
        except OSError as exc:
            critical_detailed_message(self, self.tr("Failed to save preview image"), exc)

    def _on_download_error(self, url: QUrl, error: str):
        if self._pending_downloads.pop(url.toString(), None) is None:
            return
        critical_detailed_message(self, self.tr("Failed to download preview image"), error)

    def _copy(self, size: dict):
        self._copy_downloader.start_download(QUrl(size["url"]))

    def _on_image_downloaded(self, image):
        if not image.isNull():
            QGuiApplication.clipboard().setImage(image)

    def _on_copy_error(self, error: str):
        critical_detailed_message(self, self.tr("Failed to copy preview image"), error)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
        return sanitized or "preview"


class VideoDetailsWidget(QWidget):
    def __init__(self, settings: Settings, model: ResultTableModel, parent: QWidget = None):
        super().__init__(parent)
        self._settings: Settings = settings
        self._model: ResultTableModel = model
        self._model.dataChanged.connect(self._on_model_data_changed)
        self._current_index: QModelIndex = None
        self._logo_downloader = ImageDownloader()
        self._logo_downloader.finished.connect(self._on_logo_download_finished)
        self._logo_downloader.error.connect(self._on_download_error)

        self._preview_actions_menu = PreviewActionsMenu(self._settings, PreviewActionsMenu.Actions.All, self)

        spacing = 10
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()

        self._preview_label = PixmapLabel(main_widget)
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._preview_label.customContextMenuRequested.connect(self._show_preview_actions_menu)
        self._preview_label.installEventFilter(self)
        main_layout.addWidget(self._preview_label)

        self._preview_actions_button = QToolButton(self._preview_label)
        self._preview_actions_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self._preview_actions_button.setToolTip(self.tr("Download or copy preview image"))
        self._preview_actions_button.setAutoRaise(True)
        self._preview_actions_button.clicked.connect(self._show_preview_actions_menu_at_button)
        self._preview_actions_button.hide()

        self._title_label = QLabel(main_widget)
        self._title_label.setStyleSheet("font-weight: bold")
        self._title_label.setToolTip(self._model.FieldNames[ResultFields.VideoTitle])
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title_label.setOpenExternalLinks(True)
        self._title_label.setWordWrap(True)
        main_layout.addWidget(self._title_label)

        self._duration_label = QLabel(main_widget)
        self._duration_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._duration_label.setToolTip(self._model.FieldNames[ResultFields.VideoDuration])
        main_layout.addWidget(self._duration_label)
        main_layout.addSpacing(spacing)

        channel_layout = QGridLayout()
        self._channel_logo_label = PixmapLabel(main_widget)
        self._channel_logo_label.setFixedSize(QSize(40, 40))
        channel_layout.addWidget(self._channel_logo_label, 0, 0, 0, 1)

        self._channel_title_label = QLabel(main_widget)
        self._channel_title_label.setToolTip(self._model.FieldNames[ResultFields.ChannelTitle])
        self._channel_title_label.setTextFormat(Qt.TextFormat.RichText)
        self._channel_title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._channel_title_label.setOpenExternalLinks(True)
        channel_layout.addWidget(self._channel_title_label, 0, 1)

        self._subscribers_label = QLabel(main_widget)
        self._subscribers_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._subscribers_label.setToolTip(self._model.FieldNames[ResultFields.ChannelSubscribers])
        channel_layout.addWidget(self._subscribers_label, 1, 1)
        main_layout.addLayout(channel_layout)
        main_layout.addSpacing(spacing)

        views_layout = QHBoxLayout()
        self._views_label = QLabel(main_widget)
        self._views_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._views_label.setToolTip(self._model.FieldNames[ResultFields.VideoViews])
        views_layout.addWidget(self._views_label)

        self._published_time_label = QLabel(main_widget)
        self._published_time_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._published_time_label.setToolTip(self._model.FieldNames[ResultFields.VideoPublishedTime])
        views_layout.addWidget(self._published_time_label)
        main_layout.addLayout(views_layout)
        main_layout.addSpacing(spacing)

        self._views_rate_label = QLabel(main_widget)
        self._views_rate_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._views_rate_label.setToolTip(self._model.FieldNames[ResultFields.ViewRate])
        main_layout.addWidget(self._views_rate_label)

        main_layout.addWidget(QLabel(self.tr("Tags:")))
        self._tags_edit = QTextEdit(main_widget)
        self._tags_edit.setToolTip(self.tr("The video tags"))
        self._tags_edit.setReadOnly(True)
        self._tags_edit.setPlaceholderText(self.tr("No tags"))
        main_layout.addWidget(self._tags_edit)

        main_widget.setLayout(main_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)

        self._stacked_layout = QStackedLayout()
        self._stacked_layout.setContentsMargins(0, 0, 0, 0)
        no_video_selected_label = QLabel(self.tr("Select a video to see its details"), self)
        no_video_selected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stacked_layout.addWidget(no_video_selected_label)
        self._stacked_layout.addWidget(scroll_area)
        self._stacked_layout.setCurrentIndex(0)
        self.setLayout(self._stacked_layout)

    def set_current_index(self, index: QModelIndex):
        self._current_index = index
        if index is None:
            self.clear()
            return

        row_data = self._model.get_row_data(index.row())
        if row_data is None:
            self.clear()
            return

        self._title_label.setText("<a href=\"" + row_data[ResultFields.VideoLink] + "\">" +
                                  row_data[ResultFields.VideoTitle] + "</a>")
        self._duration_label.setText(row_data[ResultFields.VideoDuration])
        self._channel_title_label.setText("<a href=\"" + row_data[ResultFields.ChannelLink] + "\">" +
                                          row_data[ResultFields.ChannelTitle] + "</a>")
        update_subscribers = '{0:,}'.format(row_data[ResultFields.ChannelSubscribers]).replace(',', ' ')
        self._subscribers_label.setText(update_subscribers + self.tr(" subscribers"))
        update_views = '{0:,}'.format(row_data[ResultFields.VideoViews]).replace(',', ' ')
        self._views_label.setText(update_views + self.tr(" views"))
        self._published_time_label.setText(row_data[ResultFields.VideoPublishedTime])
        self._views_rate_label.setText(self._model.FieldNames[ResultFields.ViewRate] + ": " + row_data[ResultFields.ViewRate])
        self._preview_label.clear()
        self._channel_logo_label.clear()

        preview_image = self._model.get_video_preview_image(index.row())
        if preview_image:
            self._preview_label.setPixmap(QPixmap.fromImage(preview_image))
        self._preview_actions_menu.set_current_video(
            row_data[ResultFields.VideoTitle], self._model.get_video_preview_sizes(index.row()))
        if self._preview_actions_menu.has_sizes():
            self._reposition_preview_actions_button()
            self._preview_actions_button.show()
        else:
            self._preview_actions_button.hide()
        logo_url = QUrl.fromUserInput(row_data[ResultFields.ChannelLogoLink])
        self._logo_downloader.start_download(logo_url)

        tags = row_data[ResultFields.VideoTags]
        if tags:
            self._tags_edit.setText(", ".join(tags))
        else:
            self._tags_edit.clear()

        self._stacked_layout.setCurrentIndex(1)

    def clear(self):
        self._current_index = None
        self._preview_actions_menu.set_current_video("", [])
        self._preview_actions_button.hide()
        self._logo_downloader.clear_cache()
        self._title_label.clear()
        self._duration_label.clear()
        self._channel_title_label.clear()
        self._subscribers_label.clear()
        self._views_label.clear()
        self._published_time_label.clear()
        self._views_rate_label.clear()
        self._preview_label.setPixmap(None)
        self._preview_label.clear()
        self._channel_logo_label.setPixmap(None)
        self._channel_logo_label.clear()
        self._tags_edit.clear()
        self._stacked_layout.setCurrentIndex(0)

    def _on_model_data_changed(self, from_index, to_index, roles):
        if self._current_index is None:
            return
        if from_index.row() == self._current_index.row() and Qt.ItemDataRole.DecorationRole in roles:
            preview_image = self._model.get_video_preview_image(self._current_index.row())
            if preview_image:
                self._preview_label.setPixmap(QPixmap.fromImage(preview_image))

    def _on_logo_download_finished(self, image):
        logo_pixmap = QPixmap.fromImage(image)
        if not logo_pixmap.isNull():
            self._channel_logo_label.setPixmap(logo_pixmap)

    def _on_download_error(self, error):
        print(self.tr("Download error: ") + error)

    def eventFilter(self, obj, event):
        if obj is self._preview_label and event.type() == QEvent.Type.Resize:
            self._reposition_preview_actions_button()
        return super().eventFilter(obj, event)

    def _reposition_preview_actions_button(self):
        margin = 4
        button_size = self._preview_actions_button.sizeHint()
        x = self._preview_label.width() - button_size.width() - margin
        self._preview_actions_button.move(max(0, x), margin)

    def _show_preview_actions_menu(self, pos):
        if self._preview_actions_menu.has_sizes():
            self._preview_actions_menu.exec(self._preview_label.mapToGlobal(pos))

    def _show_preview_actions_menu_at_button(self):
        if self._preview_actions_menu.has_sizes():
            self._preview_actions_menu.exec(
                self._preview_actions_button.mapToGlobal(self._preview_actions_button.rect().bottomLeft()))


class AnalyticsWidget(QWidget):
    def __init__(self, proxy_model: ResultSortFilterProxyModel, parent: QWidget = None):
        super().__init__(parent)
        self._current_index_following = True
        self._charts = []

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self._chart_combobox = QComboBox()
        self._chart_combobox.addItem(self.tr("Channels distribution chart"))
        self._chart_combobox.addItem(self.tr("Video duration chart"))
        self._chart_combobox.addItem(self.tr("Popular title words chart"))

        self._chart_combobox.currentIndexChanged.connect(self._on_current_chart_changed)
        main_layout.addWidget(self._chart_combobox)

        self._chart_view = QChartView()
        self._chart_view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self._chart_view)

        channels_pie_chart = ChannelsPieChart(proxy_model)
        self._charts.append(channels_pie_chart)

        video_duration_chart = VideoDurationChart(proxy_model)
        self._charts.append(video_duration_chart)

        words_pie_chart = WordsPieChart(proxy_model)
        self._charts.append(words_pie_chart)

        self._chart_view.setChart(channels_pie_chart)

    def set_current_index(self, index: QModelIndex):
        target_index = index if self._current_index_following else None
        for chart in self._charts:
            chart.set_current_index(target_index)

    def set_current_index_following(self, follow):
        self._current_index_following = follow
        if not follow:
            self.set_current_index(None)

    def set_current_chart_index(self, chart_index: int):
        self._chart_combobox.setCurrentIndex(chart_index)

    def get_current_chart_index(self):
        return self._chart_combobox.currentIndex()

    def set_charts_theme(self, theme):
        for chart in self._charts:
            chart.setTheme(theme)
            chart.rebuild()

    def _on_current_chart_changed(self, chart_index: int):
        self._chart_view.setChart(self._charts[chart_index])


class ExportPanel(QWidget):
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
        main_layout.addWidget(self._format_combo)

        self._follow_table_filters_checkbox = QCheckBox(self.tr("Follow table filters and sort order"))
        self._follow_table_filters_checkbox.setChecked(self._settings.get(Settings.ExportFollowTableFilters))
        self._follow_table_filters_checkbox.toggled.connect(self._on_follow_table_filters_toggled)
        main_layout.addWidget(self._follow_table_filters_checkbox)

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
        selected_columns = self._load_selected_columns()
        self._column_checkboxes: list[QCheckBox] = []
        for column in self._exportable_columns:
            checkbox = QCheckBox(model.FieldNames[column])
            checkbox.setChecked(column in selected_columns)
            checkbox.toggled.connect(self._on_column_checkbox_toggled)
            main_layout.addWidget(checkbox)
            self._column_checkboxes.append(checkbox)

        export_button = QPushButton(self.tr("Export..."))
        export_button.clicked.connect(self._export)
        main_layout.addWidget(export_button)

        main_layout.addStretch()

    def _on_follow_table_filters_toggled(self, checked: bool):
        self._settings.set(Settings.ExportFollowTableFilters, checked)

    def _load_selected_columns(self) -> set[int]:
        stored = self._settings.get(Settings.ExportSelectedColumns)
        if stored is None:
            return set(self._exportable_columns)
        if stored == "":
            return set()
        return set(int(column) for column in stored.split(","))

    def _selected_columns(self) -> list[int]:
        return [column for column, checkbox in zip(self._exportable_columns, self._column_checkboxes)
                if checkbox.isChecked()]

    def _save_selected_columns(self):
        selected = self._selected_columns()
        self._settings.set(Settings.ExportSelectedColumns, ",".join(str(column) for column in selected))

    def _on_column_checkbox_toggled(self, checked: bool):
        self._save_selected_columns()

    def _on_select_all_columns_clicked(self):
        self._set_all_columns_checked(True)

    def _on_select_none_columns_clicked(self):
        self._set_all_columns_checked(False)

    def _set_all_columns_checked(self, checked: bool):
        for checkbox in self._column_checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        self._save_selected_columns()

    def _export(self):
        export_format, caption, filter, file_suffix = self._format_combo.currentData()
        export_func = {"xlsx": export_to_xlsx, "csv": export_to_csv, "html": export_to_html}[export_format]
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
        export_func(file_name, export_model, selected_columns)


class VideoTableToolsPanel(StateSaveable, QWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        StateSaveable.__init__(self, settings)
        QWidget.__init__(self, parent)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._header_layout: QHBoxLayout = QHBoxLayout()
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.addStretch()
        main_layout.addLayout(self._header_layout)

        self._panel_widget: QFrame = QFrame()
        self._panel_widget.setFrameShape(QFrame.Shape.StyledPanel)
        self._panel_widget.setLayout(QStackedLayout())
        self._panel_widget.setVisible(False)
        main_layout.addWidget(self._panel_widget)

        self._header_button_group: QButtonGroup = QButtonGroup()
        self._header_button_group.setExclusive(True)
        self._header_button_group.buttonClicked.connect(self._on_header_button_clicked)
        self._checked_button: QPushButton = None

    def add_tool_panel(self, name: str, on_tool_tip: str, off_tooltip: str, panel: QWidget):
        panel_layout: QStackedLayout = self._panel_widget.layout()
        new_tab_index: int = panel_layout.count()

        button: QPushButton = QPushButton(name)
        button.setCheckable(True)
        button.setChecked(False)
        button.toggled.connect(lambda checked:
                               button.setToolTip(on_tool_tip) if checked else button.setToolTip(off_tooltip))
        self._header_button_group.addButton(button, new_tab_index)
        self._header_layout.insertWidget(self._header_layout.count() - 1, button)

        panel_layout.addWidget(panel)

    def load_state(self):
        active_panel_index: int = int(self._settings.get(Settings.ActiveToolPanelIndex))
        button_to_check: QPushButton = self._header_button_group.button(active_panel_index)
        if button_to_check:
            button_to_check.setChecked(True)
            self._on_header_button_clicked(button_to_check)
        panel_widget: StateSaveable
        for panel_widget in self._panel_widget.findChildren(StateSaveable, options=Qt.FindChildOption.FindDirectChildrenOnly):
            panel_widget.load_state()

    def save_state(self):
        active_panel_index: int = self._header_button_group.checkedId()
        self._settings.set(Settings.ActiveToolPanelIndex, active_panel_index)
        panel_widget: StateSaveable
        for panel_widget in self._panel_widget.findChildren(StateSaveable, options=Qt.FindChildOption.FindDirectChildrenOnly):
            panel_widget.save_state()

    def _on_header_button_clicked(self, button: QPushButton):
        if self._checked_button and self._checked_button == button:
            self._header_button_group.setExclusive(False)
            button.setChecked(False)
            self._header_button_group.setExclusive(True)
            self._checked_button = None
            self._panel_widget.setVisible(False)
        else:
            view_index: int = self._header_button_group.id(button)
            panel_layout: QStackedLayout = self._panel_widget.layout()
            panel_layout.setCurrentIndex(view_index)
            self._panel_widget.setVisible(True)
            self._checked_button = button


class ViewPanel(StateSaveable, QWidget):
    mode_changed = Signal(ResultTableModel.Mode)
    scale_changed = Signal(float)

    def __init__(self, settings: Settings, model: ResultSortFilterProxyModel, parent=None):
        StateSaveable.__init__(self, settings)
        QWidget.__init__(self, parent)

        main_layout: QHBoxLayout = QHBoxLayout()
        self._extra_stacked_layout: QStackedLayout = QStackedLayout()
        self._extra_stacked_layout.setContentsMargins(0, 0, 0, 0)

        self._table_view_radio: QRadioButton = QRadioButton(self.tr("Table"))
        self._table_view_radio.setChecked(True)
        self._table_view_radio.toggled.connect(lambda: self._on_view_mode_button_clicked(ResultTableModel.Mode.Normal))
        main_layout.addWidget(self._table_view_radio)
        self._extra_stacked_layout.addWidget(QWidget())

        self._gallery_view_radio = QRadioButton(self.tr("Gallery"))
        self._gallery_view_radio.toggled.connect(lambda: self._on_view_mode_button_clicked(ResultTableModel.Mode.Image))
        main_layout.addWidget(self._gallery_view_radio)
        gallery_extra_tools: QWidget = QWidget()
        gallery_extra_tools.setLayout(QHBoxLayout())
        gallery_extra_tools.layout().addWidget(QLabel(self.tr("Scale:")))
        self._scale_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setToolTip(self.tr("Change scale of gallery images"))
        self._scale_slider.setMinimum(50)
        self._scale_slider.setMaximum(250)
        self._scale_slider.setValue(100)
        self._scale_slider.valueChanged.connect(lambda: self.scale_changed.emit(self._get_scale_value()))
        gallery_extra_tools.layout().addWidget(self._scale_slider)
        self._extra_stacked_layout.addWidget(gallery_extra_tools)

        self._extra_stacked_layout.setCurrentIndex(0)
        main_layout.addLayout(self._extra_stacked_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_state(self):
        if int(self._settings.get(Settings.VideoTableMode)) == ResultTableModel.Mode.Image:
            self._gallery_view_radio.setChecked(True)
        else:
            self._table_view_radio.setChecked(True)
        self._scale_slider.setValue(int(self._settings.get(Settings.PreviewScaleIndex)))

    def save_state(self):
        if self._gallery_view_radio.isChecked():
            self._settings.set(Settings.VideoTableMode, ResultTableModel.Mode.Image)
        else:
            self._settings.set(Settings.VideoTableMode, ResultTableModel.Mode.Normal)
        self._settings.set(Settings.PreviewScaleIndex, self._scale_slider.value())

    def _get_scale_value(self):
        return self._scale_slider.value() / 100

    def _on_view_mode_button_clicked(self, mode: ResultTableModel.Mode):
        self._extra_stacked_layout.setCurrentIndex(mode)
        self.mode_changed.emit(mode)


class AbstractVideoTableWorkspace(WorkspaceWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        WorkspaceWidget.__init__(self, settings, parent)

        self._history: list[tuple] = []  # [(row_data, context)]
        self._history_index: int = -1

        h_layout: QHBoxLayout = QHBoxLayout()

        self._history_back_button = QToolButton()
        self._history_back_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self._history_back_button.setToolTip(self.tr("Go to the previous results"))
        self._history_back_button.setEnabled(False)
        self._history_back_button.clicked.connect(self._on_history_back)
        h_layout.addWidget(self._history_back_button)

        self._history_forward_button = QToolButton()
        self._history_forward_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self._history_forward_button.setToolTip(self.tr("Go to the next results"))
        self._history_forward_button.setEnabled(False)
        self._history_forward_button.clicked.connect(self._on_history_forward)
        h_layout.addWidget(self._history_forward_button)

        self._create_toolbar(h_layout)

        self._search_limit_spin_box = QSpinBox()
        self._search_limit_spin_box.setToolTip(self.tr("Set the search result limit"))
        self._search_limit_spin_box.setMinimumWidth(50)
        self._search_limit_spin_box.setRange(2, 200)
        self._search_limit_spin_box.setValue(10)
        h_layout.addWidget(self._search_limit_spin_box)
        self._search_button = QPushButton(self.tr("Search"))
        self._search_button.setToolTip(self.tr("Click to start searching"))
        self._search_button.clicked.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_button)

        self.model: ResultTableModel = ResultTableModel(self)
        self._sort_model: ResultSortFilterProxyModel = ResultSortFilterProxyModel(self)
        self._sort_model.setSourceModel(self.model)
        self._sort_model.rowsInserted.connect(self._on_insert_widgets)
        self._sort_model.rowsRemoved.connect(self._on_insert_widgets)

        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0, 0, 0, 0)

        self._tools_panel = VideoTableToolsPanel(settings, self)

        self._filters_panel = FiltersPanel(self._settings, self._sort_model)
        self._tools_panel.add_tool_panel(self.tr("Filters"), self.tr("Hide filters panel"), self.tr("Show filters panel"),
                                         self._filters_panel)

        view_panel = ViewPanel(settings, self)
        view_panel.mode_changed.connect(self._on_view_mode_changed)
        view_panel.scale_changed.connect(self._on_preview_scale_changed)
        self._tools_panel.add_tool_panel(self.tr("View"), self.tr("Hide view panel"), self.tr("Show view panel"),
                                         view_panel)

        central_layout.addWidget(self._tools_panel)

        self._stacked_layout = QStackedLayout()

        self._table_view = QTableView(self)
        self._table_view.setModel(self._sort_model)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionsMovable(True)
        self._table_view.selectionModel().selectionChanged.connect(self._on_table_row_changed)

        self._stacked_layout.addWidget(self._table_view)

        copy_video_title_action = self._table_view.addAction(self.tr("Copy video title"))
        copy_video_title_action.setData(ResultFields.VideoTitle)
        copy_video_title_action.triggered.connect(self._on_copy_action)
        copy_video_link_action = self._table_view.addAction(self.tr("Copy video link"))
        copy_video_link_action.setData(ResultFields.VideoLink)
        copy_video_link_action.triggered.connect(self._on_copy_action)
        copy_channel_title_action = self._table_view.addAction(self.tr("Copy channel title"))
        copy_channel_title_action.setData(ResultFields.ChannelTitle)
        copy_channel_title_action.triggered.connect(self._on_copy_action)
        copy_channel_link_action = self._table_view.addAction(self.tr("Copy channel link"))
        copy_channel_link_action.setData(ResultFields.ChannelLink)
        copy_channel_link_action.triggered.connect(self._on_copy_action)
        copy_published_time_action = self._table_view.addAction(self.tr("Copy published time"))
        copy_published_time_action.setData(ResultFields.VideoPublishedTime)
        copy_published_time_action.triggered.connect(self._on_copy_action)
        copy_video_duration_action = self._table_view.addAction(self.tr("Copy duration"))
        copy_video_duration_action.setData(ResultFields.VideoDuration)
        copy_video_duration_action.triggered.connect(self._on_copy_action)
        copy_video_views_action = self._table_view.addAction(self.tr("Copy views"))
        copy_video_views_action.setData(ResultFields.VideoViews)
        copy_video_views_action.triggered.connect(self._on_copy_action)
        copy_channel_subscribers_action = self._table_view.addAction(self.tr("Copy subscribers"))
        copy_channel_subscribers_action.setData(ResultFields.ChannelSubscribers)
        copy_channel_subscribers_action.triggered.connect(self._on_copy_action)
        copy_view_subscribers_action = self._table_view.addAction(self.tr("Copy views/subscribers"))
        copy_view_subscribers_action.setData(ResultFields.ViewRate)
        copy_view_subscribers_action.triggered.connect(self._on_copy_action)

        self._preview_actions_menu = PreviewActionsMenu(self._settings, PreviewActionsMenu.Actions.Copy, self._table_view)
        self._table_view.addActions(self._preview_actions_menu.actions())

        self._list_vew = QListView()
        self._list_vew.setViewMode(QListView.ViewMode.IconMode)
        self._list_vew.setResizeMode(QListView.ResizeMode.Adjust)
        self._list_vew.setIconSize(QSize(160, 90))
        self._list_vew.setUniformItemSizes(True)
        self._list_vew.setModel(self._sort_model)
        self._list_vew.setModelColumn(1)
        self._list_vew.setSelectionModel(self._table_view.selectionModel())
        self.model.dataChanged.connect(
            lambda s_index, e_index, roles:
                self._list_vew.viewport().update() if Qt.ItemDataRole.DecorationRole in roles else None)
        self._stacked_layout.addWidget(self._list_vew)
        self._on_preview_scale_changed(1.0)

        self._stacked_layout.setCurrentIndex(0)

        central_layout.addLayout(self._stacked_layout, 2)

        self._side_tab_widget = FixedTabWidget()

        self._details_widget = VideoDetailsWidget(self._settings, self.model, self)
        self._side_tab_widget.addTab(self._details_widget, self.tr("Details"))

        self._analytics_widget = AnalyticsWidget(self._sort_model, self)
        self._side_tab_widget.addTab(self._analytics_widget, self.tr("Analytics"))
        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)
        self._analytics_widget.set_current_chart_index(int(self._settings.get(Settings.LastActiveChartIndex)))

        self._export_panel = ExportPanel(self._settings, self.model, self._sort_model, self.get_data_name, self)
        self._side_tab_widget.addTab(self._export_panel, self.tr("Export"))
        self._export_panel.setEnabled(self.model.rowCount() > 0)
        self.model.rowsInserted.connect(self._update_export_panel_enabled)
        self.model.rowsRemoved.connect(self._update_export_panel_enabled)
        self.model.modelReset.connect(self._update_export_panel_enabled)

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.addWidget(central_widget)
        self._main_splitter.addWidget(self._side_tab_widget)
        self._main_splitter.setCollapsible(0, False)
        self._main_splitter.setStretchFactor(0, 3)
        self._main_splitter.setStretchFactor(1, 1)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        h_line = QFrame()
        h_line.setFrameShape(QFrame.Shape.HLine)
        h_line.setFrameShadow(QFrame.Shadow.Sunken)
        v_layout.addWidget(h_line)
        v_layout.addWidget(self._main_splitter)
        self.setLayout(v_layout)

    def has_data_to_export(self):
        return True

    def get_data_name(self):
        raise "AbstractVideoTableWorkspace.get_data_name is not implemented"

    def load_state(self):
        request_limit = int(self._settings.get(Settings.RequestLimit))
        self._search_limit_spin_box.setValue(request_limit)

        # Restore main splitter
        splitter_state = self._settings.get(Settings.MainSplitterState)
        if splitter_state and not splitter_state.isEmpty():
            self._main_splitter.restoreState(splitter_state)

        side_tab_index: int = int(self._settings.get(Settings.LastActiveDetailsTab))
        self._side_tab_widget.setCurrentIndex(side_tab_index)

        # Restore main table
        table_header_state = self._settings.get(Settings.MainTableHeaderState)
        if not table_header_state.isEmpty():
            self._table_view.horizontalHeader().restoreState(table_header_state)
        self._table_view.resizeColumnsToContents()

        self._tools_panel.load_state()

    def save_state(self):
        self._settings.set(Settings.RequestLimit, self._search_limit_spin_box.value())
        self._settings.set(Settings.LastActiveChartIndex, self._analytics_widget.get_current_chart_index())
        self._settings.set(Settings.MainTableHeaderState, self._table_view.horizontalHeader().saveState())
        self._settings.set(Settings.MainSplitterState, self._main_splitter.saveState())
        if self.isVisible():
            self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.currentIndex())
        else:  # If QTabWidget is hidden, the current index becomes 0. So we need to save the last visible index
            self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.get_last_visible_index())
        self._tools_panel.save_state()

    def add_context_menu_action(self, action_text: str) -> QAction:
        return self._table_view.addAction(action_text)

    def clear_selection(self):
        self._table_view.clearSelection()
        self._table_view.setCurrentIndex(QModelIndex())

    def show_export_tab(self):
        self._side_tab_widget.setCurrentWidget(self._export_panel)

    def get_current_row_data(self) -> list | None:
        current_index: QModelIndex = self._table_view.currentIndex()
        if not current_index.isValid():
            return None
        source_index: QModelIndex = self._sort_model.mapToSource(current_index)
        return self.model.get_row_data(source_index.row())

    def handle_preferences_change(self):
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)

        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if self._settings.get(Settings.AnalyticsFollowTableSelect):
            self._analytics_widget.set_current_index(self._table_view.currentIndex())

    def _create_toolbar(self, h_layout: QHBoxLayout):
        raise "AbstractVideoTableWorkspace._create_toolbar is not implemented"

    def _get_api_key(self, required=True):
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key and required:
            raise Exception(self.tr("YouTube API key is not set. Please set it in the preferences"))
        return api_key

    def _get_request_limit(self):
        request_limit: int = self._search_limit_spin_box.value()
        if not request_limit:
            request_limit = 10
            print("Request limit is not set. Using '10' by default")
        return request_limit

    def _get_request_page_limit(self):
        request_page_limit: int = int(self._settings.get(Settings.RequestPageLimit))
        if not request_page_limit:
            request_page_limit = 25
            print("Request page limit is not set. Using '25' by default")
        return request_page_limit

    def _on_search_clicked(self):
        raise "AbstractVideoTableWorkspace._on_search_clicked is not implemented"

    def _get_history_context(self):
        return None

    def _restore_history_context(self, context):
        pass

    def _push_history(self):
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
        self._history.append((self.model.get_data(), self._get_history_context()))

        history_limit: int = int(self._settings.get(Settings.HistoryLimit))
        if history_limit > 0 and len(self._history) > history_limit:
            self._history = self._history[-history_limit:]

        self._history_index = len(self._history) - 1
        self._update_history_buttons()

    def _on_history_back(self):
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._apply_history_entry()

    def _on_history_forward(self):
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._apply_history_entry()

    def _apply_history_entry(self):
        row_data, context = self._history[self._history_index]
        self.model.set_data(row_data)
        self._sort_model.sort(-1)
        self._details_widget.clear()
        self._on_insert_widgets()
        self._table_view.resizeColumnsToContents()
        self._restore_history_context(context)
        self._update_history_buttons()

    def _update_history_buttons(self):
        self._history_back_button.setEnabled(self._history_index > 0)
        self._history_forward_button.setEnabled(self._history_index < len(self._history) - 1)

    def _on_view_mode_changed(self, mode: ResultTableModel.Mode):
        self.model.set_mode(mode)
        if mode == ResultTableModel.Mode.Normal:
            self._stacked_layout.setCurrentIndex(0)
            self._on_insert_widgets()
        else:
            self._stacked_layout.setCurrentIndex(1)

    def _on_preview_scale_changed(self, scale: float):
        TitleFieldHeightPx: int = 60
        self.model.set_preview_scale(scale)
        item_height: int = self.model.get_preview_size().height() + TitleFieldHeightPx
        self._list_vew.setStyleSheet(f"QListView::item {{ height: {item_height}; }}")

    def _on_table_row_changed(self, current: QItemSelection, _previous: QItemSelection):
        proxy_indexes = current.indexes()
        if len(proxy_indexes) > 0:
            source_index = self._sort_model.mapToSource(proxy_indexes[0])
            self._details_widget.set_current_index(source_index)
            self._analytics_widget.set_current_index(proxy_indexes[0])
            row_data = self.model.get_row_data(source_index.row())
            video_title = row_data[ResultFields.VideoTitle] if row_data else ""
            self._preview_actions_menu.set_current_video(
                video_title, self.model.get_video_preview_sizes(source_index.row()))
        else:
            self._details_widget.set_current_index(None)
            self._analytics_widget.set_current_index(None)
            self._preview_actions_menu.set_current_video("", [])

    def _update_export_panel_enabled(self, *_args):
        self._export_panel.setEnabled(self.model.rowCount() > 0)

    def _on_copy_action(self):
        field = self.sender().data()
        index = self._table_view.currentIndex()
        if index:
            source_index = self._sort_model.mapToSource(index)
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(str(self.model.get_field_data(source_index.row(), field)))

    def _on_insert_widgets(self):
        for row in range(self._sort_model.rowCount()):
            video_idx = self._sort_model.index(row, self.model.map_field_to_table_column(ResultFields.VideoTitle))
            widget = self._table_view.indexWidget(video_idx)
            if not widget:
                source_row = self._sort_model.mapToSource(video_idx).row()
                video_item = self.model.get_row_data(source_row)
                video_label = create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label)

                channel_idx = self._sort_model.index(row, self.model.map_field_to_table_column(ResultFields.ChannelTitle))
                channel_label = create_link_label(video_item[ResultFields.ChannelLink], video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label)
