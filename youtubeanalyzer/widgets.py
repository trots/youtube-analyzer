from PySide6.QtCore import (
    QSize,
    Qt,
    QModelIndex,
    QUrl,
    QTimer,
    QStringListModel,
    QSortFilterProxyModel,
    QItemSelection
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QResizeEvent,
    QPainter
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
    QLineEdit,
    QCompleter,
    QPushButton,
    QTabWidget,
    QSizePolicy,
    QMessageBox,
    QSpinBox,
    QTableView,
    QSplitter
)
from PySide6.QtCharts import (
    QChartView,
    QChart
)
from youtubeanalyzer.theme import (
    Theme
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    ImageDownloader,
    SearchAutocompleteDownloader
)
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel
)
from youtubeanalyzer.chart import (
    ChannelsPieChart,
    VideoDurationChart,
    WordsPieChart
)


def create_link_label(link: str, text: str):
    label = QLabel("<a href=\"" + link + "\">" + text + "</a>")
    label_size_policy = label.sizePolicy()
    label_size_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
    label.setSizePolicy(label_size_policy)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(True)
    return label


def critial_detailed_message(parent, title, text, details_text):
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setDetailedText(details_text)
    return dialog.exec()


class PixmapLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1, 1)
        self.setScaledContents(False)
        self._pixmap = None

    def setPixmap(self, pixmap: QPixmap | QImage | str):
        self._pixmap = pixmap
        scaled_pixmap = self._scaled_pixmap()
        if scaled_pixmap is not None:
            return super().setPixmap(scaled_pixmap)

    def heightForWidth(self, width: int):
        if self._pixmap is None or self._pixmap.width() == 0:
            return self.height()
        return self._pixmap.height() * width / self._pixmap.width()

    def sizeHint(self):
        width = self.width()
        return QSize(width, self.heightForWidth(width))

    def resizeEvent(self, _event: QResizeEvent):
        if self._pixmap is not None:
            QTimer.singleShot(0, self, self._set_pixmap_delayed)

    def _scaled_pixmap(self):
        if self._pixmap is None or self._pixmap.width() == 0:
            return None
        return self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def _set_pixmap_delayed(self):
        scaled_pixmap = self._scaled_pixmap()
        if scaled_pixmap is not None:
            super().setPixmap(scaled_pixmap)


class VideoDetailsWidget(QWidget):
    def __init__(self, model: ResultTableModel, parent: QWidget = None):
        super().__init__(parent)
        self._model = model
        self._preview_downloader = ImageDownloader()
        self._preview_downloader.finished.connect(self._on_preview_download_finished)
        self._preview_downloader.error.connect(self._on_download_error)
        self._logo_downloader = ImageDownloader()
        self._logo_downloader.finished.connect(self._on_logo_download_finished)
        self._logo_downloader.error.connect(self._on_download_error)

        spacing = 10
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()

        self._preview_label = PixmapLabel(main_widget)
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._preview_label)

        self._title_label = QLabel(main_widget)
        self._title_label.setStyleSheet("font-weight: bold")
        self._title_label.setToolTip(self._model.FieldNames[ResultFields.VideoTitle])
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title_label.setOpenExternalLinks(True)
        self._title_label.setWordWrap(True)
        main_layout.addWidget(self._title_label)

        self._duration_label = QLabel(main_widget)
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
        self._subscribers_label.setToolTip(self._model.FieldNames[ResultFields.ChannelSubscribers])
        channel_layout.addWidget(self._subscribers_label, 1, 1)
        main_layout.addLayout(channel_layout)
        main_layout.addSpacing(spacing)

        views_layout = QHBoxLayout()
        self._views_label = QLabel(main_widget)
        self._views_label.setToolTip(self._model.FieldNames[ResultFields.VideoViews])
        views_layout.addWidget(self._views_label)

        self._published_time_label = QLabel(main_widget)
        self._published_time_label.setToolTip(self._model.FieldNames[ResultFields.VideoPublishedTime])
        views_layout.addWidget(self._published_time_label)
        main_layout.addLayout(views_layout)
        main_layout.addSpacing(spacing)

        self._views_rate_label = QLabel(main_widget)
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
        if index is None or index.row() < 0 or index.row() >= len(self._model.result):
            self.clear()
            return

        row_data = self._model.result[index.row()]
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

        preview_url = QUrl.fromUserInput(row_data[ResultFields.VideoPreviewLink])
        self._preview_downloader.start_download(preview_url)
        logo_url = QUrl.fromUserInput(row_data[ResultFields.ChannelLogoLink])
        self._logo_downloader.start_download(logo_url)

        tags = row_data[ResultFields.VideoTags]
        if tags:
            self._tags_edit.setText(", ".join(tags))
        else:
            self._tags_edit.clear()

        self._stacked_layout.setCurrentIndex(1)

    def clear(self):
        self._preview_downloader.clear_cache()
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

    def _on_preview_download_finished(self, image):
        preview_pixmap = QPixmap.fromImage(image)
        if not preview_pixmap.isNull():
            self._preview_label.setPixmap(preview_pixmap)

    def _on_logo_download_finished(self, image):
        logo_pixmap = QPixmap.fromImage(image)
        if not logo_pixmap.isNull():
            self._channel_logo_label.setPixmap(logo_pixmap)

    def _on_download_error(self, error):
        print(self.tr("Download error: ") + error)


class AnalyticsWidget(QWidget):
    def __init__(self, model: ResultTableModel, parent: QWidget = None):
        super().__init__(parent)
        self._model = model
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

        channels_pie_chart = ChannelsPieChart(model)
        self._charts.append(channels_pie_chart)

        video_duration_chart = VideoDurationChart(model)
        self._charts.append(video_duration_chart)

        words_pie_chart = WordsPieChart(model)
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


class SearchLineEdit(QLineEdit):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.setPlaceholderText(self.tr("Enter request and press 'Search'..."))
        self.setToolTip(self.placeholderText())
        self.setClearButtonEnabled(True)
        self.textEdited.connect(self._on_text_changed)

        self._autocomplete_timer = QTimer()
        self._autocomplete_timer.setSingleShot(True)
        self._autocomplete_timer.setInterval(200)
        self._autocomplete_timer.timeout.connect(self._on_editing_timeout)

        self._autocomplete_model = QStringListModel()
        completer = QCompleter(self._autocomplete_model)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.setCompleter(completer)

        self._autocomplete_downloader = SearchAutocompleteDownloader()
        self._autocomplete_downloader.finished.connect(self._on_autocomplete_downloaded)

    def _on_text_changed(self):
        self._autocomplete_timer.start()

    def _on_editing_timeout(self):
        self._autocomplete_downloader.start_download(self.text())

    def _on_autocomplete_downloaded(self, autocomplete_list):
        self._autocomplete_model.setStringList(autocomplete_list)


class TabWorkspaceFactory(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def get_workspace_name(self) -> str:
        raise "Not implemented"

    def create_workspace_button(self) -> QPushButton:
        raise "Not implemented"

    def create_workspace_widget(self, settings, parent) -> QWidget:
        raise "Not implemented"


class TabWidget(QWidget):
    workspace_factories = []

    def __init__(self, settings: Settings, parent_tab_widget: QTabWidget, parent: QWidget = None):
        super().__init__(parent)
        self._settings = settings
        self._parent_tab_widget = parent_tab_widget
        self._current_workspace_index = -1

        self._main_stacked_layout = QStackedLayout()

        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setLayout(self._main_layout)
        self._main_stacked_layout.addWidget(container)
        self._main_stacked_layout.setCurrentIndex(0)
        self.setLayout(self._main_stacked_layout)

        self._main_layout.addStretch()
        for workspace_factory in TabWidget.workspace_factories:
            workspace_button = workspace_factory.create_workspace_button()
            workspace_button.clicked.connect(self._create_workspace)
            self._main_layout.addWidget(workspace_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addStretch()

    def current_workspace(self):
        return self._main_stacked_layout.currentWidget() if self._main_stacked_layout.currentIndex() == 1 else None

    def load_state(self):
        workspace_index = int(self._settings.get(Settings.TabWorkspaceIndex))
        if workspace_index >= 0:
            workspace_widget = self.create_workspace(workspace_index)
            workspace_widget.load_state()

    def save_state(self):
        self._settings.set(Settings.TabWorkspaceIndex, self._current_workspace_index)
        if self._current_workspace_index >= 0:
            workspace_widget = self._main_stacked_layout.currentWidget()
            workspace_widget.save_state()

    def handle_preferences_change(self):
        workspace = self.current_workspace()
        if workspace:
            workspace.handle_preferences_change()

    def create_workspace(self, workspace_index):
        if workspace_index < 0 or workspace_index >= len(TabWidget.workspace_factories):
            return
        factory = TabWidget.workspace_factories[workspace_index]
        workspace_widget = factory.create_workspace_widget(self._settings, self)
        self._main_stacked_layout.addWidget(workspace_widget)
        self._main_stacked_layout.setCurrentIndex(1)
        tab_index = self._parent_tab_widget.indexOf(self)
        self._parent_tab_widget.setTabText(tab_index, factory.get_workspace_name())
        self._current_workspace_index = workspace_index
        return workspace_widget

    def _create_workspace(self):
        workspace_button = self.sender()
        workspace_index = self._main_layout.indexOf(workspace_button) - 1
        self.create_workspace(workspace_index)


class AbstractVideoTableWorkspace(QWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(parent)

        self._settings = settings

        h_layout = QHBoxLayout()
        self._create_toolbar(h_layout)

        self._search_limit_spin_box = QSpinBox()
        self._search_limit_spin_box.setToolTip(self.tr("Set the search result limit"))
        self._search_limit_spin_box.setMinimumWidth(50)
        self._search_limit_spin_box.setRange(2, 30)
        self._search_limit_spin_box.setValue(10)
        h_layout.addWidget(self._search_limit_spin_box)
        self._search_button = QPushButton(self.tr("Search"))
        self._search_button.setToolTip(self.tr("Click to start searching"))
        self._search_button.clicked.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_button)

        self.model = ResultTableModel(self)
        self._sort_model = QSortFilterProxyModel(self)
        self._sort_model.setSortRole(ResultTableModel.SortRole)
        self._sort_model.setSourceModel(self.model)
        self._table_view = QTableView(self)
        self._table_view.setModel(self._sort_model)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionsMovable(True)
        self._table_view.selectionModel().selectionChanged.connect(self._on_table_row_changed)

        self._side_tab_widget = QTabWidget()

        self._details_widget = VideoDetailsWidget(self.model, self)
        self._side_tab_widget.addTab(self._details_widget, self.tr("Details"))

        self._analytics_widget = AnalyticsWidget(self.model, self)
        self._side_tab_widget.addTab(self._analytics_widget, self.tr("Analytics"))
        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)
        self._analytics_widget.set_current_chart_index(int(self._settings.get(Settings.LastActiveChartIndex)))

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.addWidget(self._table_view)
        self._main_splitter.addWidget(self._side_tab_widget)
        self._main_splitter.setCollapsible(0, False)
        self._main_splitter.setStretchFactor(0, 3)
        self._main_splitter.setStretchFactor(1, 1)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._main_splitter)
        self.setLayout(v_layout)

    def load_state(self):
        request_limit = int(self._settings.get(Settings.RequestLimit))
        self._search_limit_spin_box.setValue(request_limit)
        # Restore main splitter
        splitter_state = self._settings.get(Settings.MainSplitterState)
        if splitter_state and not splitter_state.isEmpty():
            self._main_splitter.restoreState(splitter_state)
        # Restore main table
        table_header_state = self._settings.get(Settings.MainTableHeaderState)
        if not table_header_state.isEmpty():
            self._table_view.horizontalHeader().restoreState(table_header_state)
        self._table_view.resizeColumnsToContents()

    def save_state(self):
        self._settings.set(Settings.RequestLimit, self._search_limit_spin_box.value())
        self._settings.set(Settings.LastActiveChartIndex, self._analytics_widget.get_current_chart_index())
        self._settings.set(Settings.MainTableHeaderState, self._table_view.horizontalHeader().saveState())
        self._settings.set(Settings.MainSplitterState, self._main_splitter.saveState())
        self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.currentIndex())

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

    def _on_search_clicked(self):
        raise "AbstractVideoTableWorkspace._on_search_clicked is not implemented"

    def _on_table_row_changed(self, current: QItemSelection, _previous: QItemSelection):
        indexes = current.indexes()
        if len(indexes) > 0:
            index = self._sort_model.mapToSource(indexes[0])
            self._details_widget.set_current_index(index)
            self._analytics_widget.set_current_index(index)
        else:
            self._details_widget.set_current_index(None)
            self._analytics_widget.set_current_index(None)
