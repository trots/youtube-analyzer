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
    QChart
)
from model import (
    ResultFields,
    ResultTableModel
)


class ChannelsPieSeries(QPieSeries):
    def __init__(self, model: ResultTableModel):
        super().__init__()
        self._current_channel = None
        self._model = model
        self._model.modelReset.connect(self.rebuild)
        self._last_pen = None
        self._last_brush = None
        self.setHoleSize(0.3)
        self.hovered.connect(self._on_slice_hovered)

    def rebuild(self):
        self.clear()
        if len(self._model.result) == 0:
            return

        channel_names = [row[ResultFields.ChannelTitle] for row in self._model.result]
        counter = Counter(channel_names)
        for name in counter:
            self.append(name, counter[name])

    def set_current_channel(self, channel_name):
        if self._current_channel == channel_name:
            return

        for slice in self.slices():
            if slice.label() == self._current_channel:
                slice.setExploded(False)
                slice.setLabelVisible(False)
                slice.setPen(self._last_pen)
                slice.setBrush(self._last_brush)
            if slice.label() == channel_name:
                slice.setExploded()
                slice.setLabelVisible()
                self._last_pen = slice.pen()
                self._last_brush = slice.brush()
                slice.setPen(QPen(Qt.darkGreen, 2))
                slice.setBrush(Qt.green)

        self._current_channel = channel_name

    def _on_slice_hovered(self, pie_slice, state):
        if pie_slice.label() == self._current_channel:
            return
        pie_slice.setLabelVisible(state)
