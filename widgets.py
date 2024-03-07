from PySide6.QtCore import (
    Qt,
    QModelIndex
)
from PySide6.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)
from model import (
    ResultFields,
    ResultTableModel
)


class VideoDetailsWidget(QWidget):
    def __init__(self, model: ResultTableModel, parent: QWidget = None):
        super().__init__(parent)
        self._model = model

        spacing = 10
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()

        self._title_label = QLabel(main_widget)
        self._title_label.setStyleSheet("font-weight: bold")
        self._title_label.setToolTip(self._model.header[ResultFields.VideoTitle])
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title_label.setOpenExternalLinks(True)
        self._title_label.setWordWrap(True)
        main_layout.addWidget(self._title_label)

        self._duration_label = QLabel(main_widget)
        self._duration_label.setToolTip(self._model.header[ResultFields.VideoDuration])
        main_layout.addWidget(self._duration_label)
        main_layout.addSpacing(spacing)

        self._channel_title_label = QLabel(main_widget)
        self._channel_title_label.setToolTip(self._model.header[ResultFields.ChannelTitle])
        self._channel_title_label.setTextFormat(Qt.TextFormat.RichText)
        self._channel_title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._channel_title_label.setOpenExternalLinks(True)
        main_layout.addWidget(self._channel_title_label)

        self._subscribers_label = QLabel(main_widget)
        self._subscribers_label.setToolTip(self._model.header[ResultFields.ChannelSubscribers])
        main_layout.addWidget(self._subscribers_label)
        main_layout.addSpacing(spacing)

        views_layout = QHBoxLayout()
        self._views_label = QLabel(main_widget)
        self._views_label.setToolTip(self._model.header[ResultFields.VideoViews])
        views_layout.addWidget(self._views_label)

        self._published_time_label = QLabel(main_widget)
        self._published_time_label.setToolTip(self._model.header[ResultFields.VideoPublishedTime])
        views_layout.addWidget(self._published_time_label)
        main_layout.addLayout(views_layout)
        main_layout.addSpacing(spacing)

        self._views_rate_label = QLabel(main_widget)
        self._views_rate_label.setToolTip(self._model.header[ResultFields.ViewRate])
        main_layout.addWidget(self._views_rate_label)

        main_layout.addStretch(1)
        main_widget.setLayout(main_layout)
        
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(scroll_area)

    def set_current_index(self, index: QModelIndex):
        if index is None:
            self._title_label.clear()
            self._duration_label.clear()
            self._channel_title_label.clear()
            self._subscribers_label.clear()
            self._views_label.clear()
            self._published_time_label.clear()
            self._views_rate_label.clear()
            return

        row = index.row()
        row_data = self._model.result[row]
        self._title_label.setText("<a href=\"" + row_data[ResultFields.VideoLink] + "\">" + row_data[ResultFields.VideoTitle] + "</a>")
        self._duration_label.setText(row_data[ResultFields.VideoDuration])
        self._channel_title_label.setText("<a href=\"" + row_data[ResultFields.ChannelLink] + "\">" + row_data[ResultFields.ChannelTitle] + "</a>")
        self._subscribers_label.setText(str(row_data[ResultFields.ChannelSubscribers]) + self.tr(" subscribers"))
        self._views_label.setText(str(row_data[ResultFields.VideoViews]) + self.tr(" views"))
        self._published_time_label.setText(row_data[ResultFields.VideoPublishedTime])
        self._views_rate_label.setText(self._model.header[ResultFields.ViewRate] + ": " + row_data[ResultFields.ViewRate])
