from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
    QItemSelection
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QSizePolicy,
    QWidget,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableView,
    QTabWidget,
    QMessageBox
)
from PySide6.QtCharts import (
    QChart
)
from theme import (
    Theme
)
from settings import (
    Settings
)
from engine import (
    YoutubeApiEngine,
    YoutubeGrepEngine
)
from model import (
    ResultFields,
    ResultTableModel
)
from widgets import (
    SearchLineEdit,
    TabWorkspaceFactory,
    VideoDetailsWidget,
    AnalyticsWidget
)


class SearchWorkspace(QWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(parent)

        self.request_text = ""
        self._settings = settings

        h_layout = QHBoxLayout()
        self._search_line_edit = SearchLineEdit()
        self._search_line_edit.returnPressed.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_line_edit)
        self._search_limit_spin_box = QSpinBox()
        self._search_limit_spin_box.setToolTip(self.tr("Set the search result limit"))
        self._search_limit_spin_box.setMinimumWidth(50)
        self._search_limit_spin_box.setRange(2, 30)
        request_limit = int(self._settings.get(Settings.RequestLimit))
        self._search_limit_spin_box.setValue(request_limit)
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

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._main_splitter)
        self.setLayout(v_layout)

    def load_state(self):
        # Restore main splitter
        splitter_state = self._settings.get(Settings.MainSplitterState)
        if not splitter_state.isEmpty():
            self._main_splitter.restoreState(splitter_state)
        # Restore main table
        table_header_state = self._settings.get(Settings.MainTableHeaderState)
        if not table_header_state.isEmpty():
            self._table_view.horizontalHeader().restoreState(table_header_state)
        self._table_view.resizeColumnsToContents()
        self._search_line_edit.setFocus()

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

    def _on_search_clicked(self):
        self.request_text = self._search_line_edit.text()

        if self.request_text == "":
            return

        self._search_line_edit.setDisabled(True)
        self._search_button.setDisabled(True)
        self._table_view.setDisabled(True)
        self._side_tab_widget.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.model.clear()
        self._sort_model.sort(-1)
        self._details_widget.clear()
        QApplication.instance().processEvents()

        engine = self._create_engine()
        if engine.search(self.request_text):
            for i in range(len(self.model.result)):
                video_idx = self._sort_model.index(i, self.model.get_field_column(ResultFields.VideoTitle))
                video_item = self.model.result[i]
                video_label = self._create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label)

                channel_idx = self._sort_model.index(i, self.model.get_field_column(ResultFields.ChannelTitle))
                channel_label = self._create_link_label(video_item[ResultFields.ChannelLink],
                                                        video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label)

            self._table_view.resizeColumnsToContents()
        else:
            dialog = QMessageBox()
            dialog.setWindowTitle(self.tr("Error"))
            dialog.setText(self.tr("Error in the searching process"))
            dialog.setIcon(QMessageBox.Critical)
            dialog.setDetailedText(engine.error)
            dialog.exec()

        QApplication.restoreOverrideCursor()
        self._search_line_edit.setDisabled(False)
        self._search_button.setDisabled(False)
        self._table_view.setDisabled(False)
        self._side_tab_widget.setDisabled(False)

    def _on_table_row_changed(self, current: QItemSelection, _previous: QItemSelection):
        indexes = current.indexes()
        if len(indexes) > 0:
            index = self._sort_model.mapToSource(indexes[0])
            self._details_widget.set_current_index(index)
            self._analytics_widget.set_current_index(index)
        else:
            self._details_widget.set_current_index(None)
            self._analytics_widget.set_current_index(None)

    def _create_engine(self):
        request_limit = self._search_limit_spin_box.value()
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            return YoutubeGrepEngine(self.model, request_limit)
        else:
            return YoutubeApiEngine(self.model, request_limit, api_key)

    def _create_link_label(self, link: str, text: str):
        label = QLabel("<a href=\"" + link + "\">" + text + "</a>")
        label_size_policy = label.sizePolicy()
        label_size_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        label.setSizePolicy(label_size_policy)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)
        return label


class SearchWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def get_workspace_name(self) -> str:
        return "Search"

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton("Search video...")
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget) -> QWidget:
        return SearchWorkspace(settings, parent)
