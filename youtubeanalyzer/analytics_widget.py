from PySide6.QtCore import (
    QModelIndex
)
from PySide6.QtGui import (
    QPainter
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox
)
from PySide6.QtCharts import (
    QChartView
)
from youtubeanalyzer.filters import (
    ResultSortFilterProxyModel
)
from youtubeanalyzer.chart import (
    ChannelsPieChart,
    VideoDurationChart,
    WordsPieChart
)


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
