from collections import (
    Counter
)
from PySide6.QtCore import (
    Qt
)
from PySide6.QtGui import (
    QPen
)
from PySide6.QtCharts import (
    QPieSeries,
    QBarSet,
    QBarSeries,
    QBarCategoryAxis,
    QChart
)
from model import (
    ResultFields,
    ResultTableModel
)


class ChannelsPieChart(QChart):
    def __init__(self, model: ResultTableModel):
        super().__init__()
        self._current_index = None
        self._model = model
        self._model.modelReset.connect(self._on_model_reset)
        self._series = QPieSeries()
        self._series.setHoleSize(0.3)
        self._series.hovered.connect(self._on_slice_hovered)
        self.addSeries(self._series)
        self._last_pen = None
        self._last_brush = None

    def rebuild(self):
        self._series.clear()
        if len(self._model.result) == 0:
            return

        channel_names = [row[ResultFields.ChannelTitle] for row in self._model.result]
        counter = Counter(channel_names)
        for name in counter:
            self._series.append(name, counter[name])

        current_index = self._current_index
        self._current_index = None
        self.set_current_index(current_index)

    def set_current_index(self, index):
        current_row = self._current_index.row() if self._current_index is not None else None
        row = index.row() if index is not None else None

        if current_row == row:
            return

        current_channel_name = self._model.get_field_data(current_row, ResultFields.ChannelTitle)

        if current_channel_name is not None:
            for slice in self._series.slices():
                if slice.label() == current_channel_name:
                    slice.setExploded(False)
                    slice.setLabelVisible(False)
                    slice.setPen(self._last_pen)
                    slice.setBrush(self._last_brush)
                    break

        channel_name = self._model.get_field_data(row, ResultFields.ChannelTitle)

        if channel_name is not None:
            for slice in self._series.slices():
                if slice.label() == channel_name:
                    slice.setExploded()
                    slice.setLabelVisible()
                    self._last_pen = slice.pen()
                    self._last_brush = slice.brush()
                    slice.setPen(QPen(Qt.darkGreen, 2))
                    slice.setBrush(Qt.green)
                    break

        self._current_index = index

    def _on_model_reset(self):
        self.set_current_index(None)
        self.rebuild()

    def _on_slice_hovered(self, pie_slice, state):
        row = self._current_index.row() if self._current_index is not None else None
        channel_name = self._model.get_field_data(row, ResultFields.ChannelTitle)
        if pie_slice.label() == channel_name:
            return
        pie_slice.setLabelVisible(state)

class VideoDurationChart(QChart):
    def __init__(self, model: ResultTableModel):
        super().__init__()
        self._current_index = None
        self._model = model
        self._model.modelReset.connect(self._on_model_reset)
        self._bar_set = None
        self._categories = [
            [300, self.tr("5m"), 0],
            [600, self.tr("10m"), 0],
            [900, self.tr("15m"), 0],
            [1200, self.tr("20m"), 0],
            [1800, self.tr("30m"), 0],
            [2700, self.tr("45m"), 0],
            [3600, self.tr("1h"), 0],
            [5400, self.tr("1,5h"), 0],
            [7200, self.tr("2h"), 0],
            [10800, self.tr("3h"), 0],
            [None, self.tr("3+h"), 0]
        ]
        self._axis_x = QBarCategoryAxis()
        self._axis_x.append([category[1] for category in self._categories])
        self.addAxis(self._axis_x, Qt.AlignBottom)
        self.legend().setVisible(False)

    def rebuild(self):
        self.removeAllSeries()
        self._bar_set = QBarSet("")
        if len(self._model.result) == 0:
            return

        for category in self._categories:
            category[2] = 0
        durations_secs = [row[ResultFields.VideoDurationTimedelta].total_seconds() for row in self._model.result]

        for i in range(len(durations_secs)):
            category_index = self._find_category_for_value(durations_secs[i])
            self._categories[category_index][2] = self._categories[category_index][2] + 1

        self._bar_set.append([category[2] for category in self._categories])
        self._bar_set.setSelectedColor(Qt.green)

        bar_series = QBarSeries()
        bar_series.append(self._bar_set)
        self.addSeries(bar_series)

    def set_current_index(self, index):
        if self._bar_set is not None:
            self._bar_set.deselectAllBars()

        if index is None:
            return

        row = index.row()
        duration = self._model.get_field_data(row, ResultFields.VideoDurationTimedelta).total_seconds()
        category_index = self._find_category_for_value(duration)
        self._bar_set.setBarSelected(category_index, True)

    def _on_model_reset(self):
        self.set_current_index(None)
        self.rebuild()

    def _find_category_for_value(self, duration:int ):
        for i in range(len(self._categories) - 1):
            if duration > self._categories[i][0]:
                continue
            return i
        return len(self._categories) - 1
