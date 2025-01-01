import pycountry
from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
    QItemSelection,
    QTimer
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QTableView,
    QTabWidget,
    QMessageBox,
    QSpinBox
)
from PySide6.QtCharts import (
    QChart
)
from youtubeanalyzer.defines import (
    app_name
)
from youtubeanalyzer.theme import (
    Theme
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    YoutubeApiEngine
)
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel
)
from youtubeanalyzer.widgets import (
    create_link_label,
    critial_detailed_message,
    TabWorkspaceFactory,
    VideoDetailsWidget,
    AnalyticsWidget
)


class TrendsWorkspace(QWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(parent)

        self._settings = settings
        self._selected_category = None
        self._loaded_category_id = None

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(self.tr("Category:")))
        self._category_combo_box = QComboBox()
        h_layout.addWidget(self._category_combo_box, 1)
        h_layout.addSpacing(10)
        h_layout.addWidget(QLabel(self.tr("Region:")))
        self._region_combo_box = QComboBox()
        for country in pycountry.countries:
            self._region_combo_box.addItem(country.name, country.alpha_2)
        h_layout.addWidget(self._region_combo_box)
        self._region_combo_box.currentIndexChanged.connect(self._update_categories)

        h_layout.addStretch(2)
        self._request_limit_spin_box = QSpinBox()
        self._request_limit_spin_box.setToolTip(self.tr("Set the result limit"))
        self._request_limit_spin_box.setMinimumWidth(50)
        self._request_limit_spin_box.setRange(2, 200)
        self._request_limit_spin_box.setValue(10)
        h_layout.addWidget(self._request_limit_spin_box)

        h_layout.addStretch()
        self._show_button = QPushButton(self.tr("Show"))
        self._show_button.setToolTip(self.tr("Click to show trends"))
        self._show_button.clicked.connect(self._on_show_trends_clicked)
        h_layout.addWidget(self._show_button)

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

        QTimer.singleShot(0, self, self._update_categories)

    def _update_categories(self):
        self._category_combo_box.clear()
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            return

        engine = YoutubeApiEngine(api_key)
        region_code = self._region_combo_box.currentData()
        if not region_code:
            region_code = "US"
        categories_lang = "ru_RU" if self._settings.get(Settings.Language) == "Ru" else "en_US"
        categories = engine.get_video_categories(region_code, categories_lang)
        if len(categories) == 0:
            critial_detailed_message(self, app_name, self.tr("Unable to get video categories"), engine.errorDetails)
        for category in categories:
            self._category_combo_box.addItem(category.text, category.id)
        if self._loaded_category_id is not None:
            index = self._category_combo_box.findData(self._loaded_category_id)
            if index >= 0:
                self._category_combo_box.setCurrentIndex(index)
            self._loaded_category_id = None

    def load_state(self):
        request_limit = int(self._settings.get(Settings.RequestLimit))
        self._request_limit_spin_box.setValue(request_limit)
        # Restore main splitter
        splitter_state = self._settings.get(Settings.MainSplitterState)
        if splitter_state and not splitter_state.isEmpty():
            self._main_splitter.restoreState(splitter_state)
        # Restore main table
        table_header_state = self._settings.get(Settings.MainTableHeaderState)
        if not table_header_state.isEmpty():
            self._table_view.horizontalHeader().restoreState(table_header_state)
        self._table_view.resizeColumnsToContents()
        self._analytics_widget.set_current_chart_index(int(self._settings.get(Settings.LastActiveChartIndex)))
        index = self._region_combo_box.findData(self._settings.get(Settings.TrendsRegion))
        if index >= 0:
            self._region_combo_box.setCurrentIndex(index)
        self._loaded_category_id = int(self._settings.get(Settings.TrendsVideoCategoryId))

    def save_state(self):
        self._settings.set(Settings.RequestLimit, self._request_limit_spin_box.value())
        self._settings.set(Settings.LastActiveChartIndex, self._analytics_widget.get_current_chart_index())
        self._settings.set(Settings.MainTableHeaderState, self._table_view.horizontalHeader().saveState())
        self._settings.set(Settings.MainSplitterState, self._main_splitter.saveState())
        self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.currentIndex())
        self._settings.set(Settings.TrendsRegion, self._region_combo_box.currentData())
        if self._category_combo_box.currentData():
            self._settings.set(Settings.TrendsVideoCategoryId, int(self._category_combo_box.currentData()))

    def handle_preferences_change(self):
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)

        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if self._settings.get(Settings.AnalyticsFollowTableSelect):
            self._analytics_widget.set_current_index(self._table_view.currentIndex())

    def _on_show_trends_clicked(self):
        self.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        self.model.clear()
        self._sort_model.sort(-1)
        self._details_widget.clear()
        QApplication.instance().processEvents()

        category_id = int(self._category_combo_box.currentData())
        if not category_id:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            QMessageBox.critical(self, app_name, self.tr("Unable to show trends. Video category is not selected."))
            return

        region_code = self._region_combo_box.currentData()
        if not region_code:
            region_code = "US"
            print("Region code is not set. Using 'US' by default")

        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            QMessageBox.critical(self, app_name, self.tr("Unable to show trends. YouTube API key is not set. \
                                                         Please set it in the preferences"))
            return

        request_limit = self._request_limit_spin_box.value()
        if not request_limit:
            request_limit = 10
            print("Request limit is not set. Using '10' by default")

        request_page_limit = int(self._settings.get(Settings.RequestPageLimit))
        if not request_page_limit:
            request_page_limit = 25
            print("Request page limit is not set. Using '25' by default")

        engine = YoutubeApiEngine(api_key, self.model, request_limit, request_page_limit)
        if engine.trends(category_id, region_code):
            for i in range(len(self.model.result)):
                video_idx = self._sort_model.index(i, self.model.get_field_column(ResultFields.VideoTitle))
                video_item = self.model.result[i]
                video_label = create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label)

                channel_idx = self._sort_model.index(i, self.model.get_field_column(ResultFields.ChannelTitle))
                channel_label = create_link_label(video_item[ResultFields.ChannelLink], video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label)

            self._table_view.resizeColumnsToContents()
        else:
            text = self.tr("Trends searching failed")
            if engine.errorReason is not None:
                text += ": " + engine.errorReason
            critial_detailed_message(self, app_name, text, engine.errorDetails)

        QApplication.restoreOverrideCursor()
        self.setDisabled(False)

    def _on_table_row_changed(self, current: QItemSelection, _previous: QItemSelection):
        indexes = current.indexes()
        if len(indexes) > 0:
            index = self._sort_model.mapToSource(indexes[0])
            self._details_widget.set_current_index(index)
            self._analytics_widget.set_current_index(index)
        else:
            self._details_widget.set_current_index(None)
            self._analytics_widget.set_current_index(None)


class TrendsWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def get_workspace_name(self) -> str:
        return "Trends"

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton("Show trends...")
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget) -> QWidget:
        return TrendsWorkspace(settings, parent)
