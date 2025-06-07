from PySide6.QtCore import (
    Signal,
    QSize,
    Qt,
    QModelIndex,
    QUrl,
    QItemSelection
)
from PySide6.QtGui import (
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
    QPushButton,
    QTabWidget,
    QSpinBox,
    QTableView,
    QSplitter,
    QFrame,
    QButtonGroup,
    QRadioButton,
    QListView,
    QSlider
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
    ImageDownloader
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
    PixmapLabel
)
from youtubeanalyzer.workspace import (
    WorkspaceWidget
)


class VideoDetailsWidget(QWidget):
    def __init__(self, model: ResultTableModel, parent: QWidget = None):
        super().__init__(parent)
        self._model: ResultTableModel = model
        self._model.dataChanged.connect(self._on_model_data_changed)
        self._current_index: QModelIndex = None
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


class ViewsPanel(StateSaveable, QWidget):
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
        self._scale_slider.setMaximum(150)
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

        h_layout: QHBoxLayout = QHBoxLayout()
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

        self.model = ResultTableModel(self)
        self._sort_model = ResultSortFilterProxyModel(self)
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

        views_panel = ViewsPanel(settings, self)
        views_panel.mode_changed.connect(self._on_view_mode_changed)
        views_panel.scale_changed.connect(lambda scale: self.model.set_preview_scale(scale))
        self._tools_panel.add_tool_panel(self.tr("Views"), self.tr("Hide views panel"), self.tr("Show views panel"),
                                         views_panel)

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

        self._list_vew = QListView()
        self._list_vew.setViewMode(QListView.ViewMode.IconMode)
        self._list_vew.setResizeMode(QListView.ResizeMode.Adjust)
        self._list_vew.setIconSize(QSize(100, 100))
        self._list_vew.setUniformItemSizes(True)
        self._list_vew.setModel(self._sort_model)
        self._list_vew.setModelColumn(1)
        self._list_vew.setSelectionModel(self._table_view.selectionModel())
        self.model.dataChanged.connect(
            lambda s_index, e_index, roles:
                self._list_vew.viewport().update() if Qt.ItemDataRole.DecorationRole in roles else None)
        self._stacked_layout.addWidget(self._list_vew)

        self._stacked_layout.setCurrentIndex(0)

        central_layout.addLayout(self._stacked_layout, 2)

        self._side_tab_widget = QTabWidget()

        self._details_widget = VideoDetailsWidget(self.model, self)
        self._side_tab_widget.addTab(self._details_widget, self.tr("Details"))

        self._analytics_widget = AnalyticsWidget(self._sort_model, self)
        self._side_tab_widget.addTab(self._analytics_widget, self.tr("Analytics"))
        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)
        self._analytics_widget.set_current_chart_index(int(self._settings.get(Settings.LastActiveChartIndex)))

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

    def get_data_name(self):
        raise "AbstractVideoTableWorkspace.get_data_name is not implemented"

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

        self._tools_panel.load_state()

    def save_state(self):
        self._settings.set(Settings.RequestLimit, self._search_limit_spin_box.value())
        self._settings.set(Settings.LastActiveChartIndex, self._analytics_widget.get_current_chart_index())
        self._settings.set(Settings.MainTableHeaderState, self._table_view.horizontalHeader().saveState())
        self._settings.set(Settings.MainSplitterState, self._main_splitter.saveState())
        self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.currentIndex())
        self._tools_panel.save_state()

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

    def _on_view_mode_changed(self, mode: ResultTableModel.Mode):
        self.model.set_mode(mode)
        if mode == ResultTableModel.Mode.Normal:
            self._stacked_layout.setCurrentIndex(0)
            self._on_insert_widgets()
        else:
            self._stacked_layout.setCurrentIndex(1)

    def _on_table_row_changed(self, current: QItemSelection, _previous: QItemSelection):
        proxy_indexes = current.indexes()
        if len(proxy_indexes) > 0:
            source_index = self._sort_model.mapToSource(proxy_indexes[0])
            self._details_widget.set_current_index(source_index)
            self._analytics_widget.set_current_index(proxy_indexes[0])
        else:
            self._details_widget.set_current_index(None)
            self._analytics_widget.set_current_index(None)

    def _on_copy_action(self):
        field = self.sender().data()
        index = self._table_view.currentIndex()
        if index:
            source_index = self._sort_model.mapToSource(index)
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(str(self.model.get_field_data(source_index.row(), field)))

    def _on_insert_widgets(self):
        for i in range(self.model.rowCount()):
            video_idx = self._sort_model.index(i, self.model.map_field_to_table_column(ResultFields.VideoTitle))
            widget = self._table_view.indexWidget(video_idx)
            if not widget:
                video_item = self.model.get_row_data(i)
                video_label = create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label)

                channel_idx = self._sort_model.index(i, self.model.map_field_to_table_column(ResultFields.ChannelTitle))
                channel_label = create_link_label(video_item[ResultFields.ChannelLink], video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label)
