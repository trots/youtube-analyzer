from PySide6.QtCore import (
    QSize,
    Qt,
    QModelIndex,
    QItemSelection
)
from PySide6.QtGui import (
    QAction,
    QGuiApplication
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
    QPushButton,
    QSpinBox,
    QTableView,
    QSplitter,
    QFrame,
    QListView,
    QToolButton,
    QStyle
)
from PySide6.QtCharts import (
    QChart
)
from youtubeanalyzer.theme import (
    Theme
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel
)
from youtubeanalyzer.filters import (
    ResultSortFilterProxyModel,
    FiltersPanel
)
from youtubeanalyzer.widgets import (
    create_link_label,
    FixedTabWidget
)
from youtubeanalyzer.workspace import (
    WorkspaceWidget
)
from youtubeanalyzer.preview_actions_menu import (
    PreviewActionsMenu
)
from youtubeanalyzer.video_details_widget import (
    VideoDetailsWidget
)
from youtubeanalyzer.analytics_widget import (
    AnalyticsWidget
)
from youtubeanalyzer.export_panel import (
    ExportPanel
)
from youtubeanalyzer.video_table_tools_panel import (
    VideoTableToolsPanel,
    ViewPanel
)


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
