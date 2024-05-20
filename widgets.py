from PySide6.QtCore import (
    QSize,
    Qt,
    QModelIndex,
    QUrl,
    QTimer
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
    QComboBox
)
from PySide6.QtCharts import (
    QChartView,
    QChart
)
from engine import (
    ImageDownloader
)
from model import (
    ResultFields,
    ResultTableModel
)
from chart import (
    ChannelsPieSeries,
    VideoDurationChart
)


class PixmapLabel(QLabel):
    def __init__(self, parent = None):
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
        main_layout.addWidget(self._preview_label, 1)

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

        channel_layout = QGridLayout()
        self._channel_logo_label = PixmapLabel(main_widget)
        self._channel_logo_label.setFixedSize(QSize(40, 40))
        channel_layout.addWidget(self._channel_logo_label, 0, 0, 0, 1)

        self._channel_title_label = QLabel(main_widget)
        self._channel_title_label.setToolTip(self._model.header[ResultFields.ChannelTitle])
        self._channel_title_label.setTextFormat(Qt.TextFormat.RichText)
        self._channel_title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._channel_title_label.setOpenExternalLinks(True)
        channel_layout.addWidget(self._channel_title_label, 0, 1)

        self._subscribers_label = QLabel(main_widget)
        self._subscribers_label.setToolTip(self._model.header[ResultFields.ChannelSubscribers])
        channel_layout.addWidget(self._subscribers_label, 1, 1)
        main_layout.addLayout(channel_layout)
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

        main_layout.addWidget(QLabel(self.tr("Tags:")))
        self._tags_edit = QTextEdit(main_widget)
        self._tags_edit.setToolTip(self.tr("The video tags"))
        self._tags_edit.setReadOnly(True)
        self._tags_edit.setPlaceholderText(self.tr("No tags"))
        main_layout.addWidget(self._tags_edit)

        main_layout.addStretch(2)
        main_widget.setLayout(main_layout)
        
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)

        self._stacked_layout = QStackedLayout()
        self._stacked_layout.setContentsMargins(0, 0, 0, 0)
        no_video_selected_label = QLabel(self.tr("Select a video to see its details"))
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
        self._title_label.setText("<a href=\"" + row_data[ResultFields.VideoLink] + "\">" + row_data[ResultFields.VideoTitle] + "</a>")
        self._duration_label.setText(row_data[ResultFields.VideoDuration])
        self._channel_title_label.setText("<a href=\"" + row_data[ResultFields.ChannelLink] + "\">" + row_data[ResultFields.ChannelTitle] + "</a>")
        update_subscribers = '{0:,}'.format(row_data[ResultFields.ChannelSubscribers]).replace(',', ' ')
        self._subscribers_label.setText(update_subscribers + self.tr(" subscribers"))
        update_views = '{0:,}'.format(row_data[ResultFields.VideoViews]).replace(',', ' ')
        self._views_label.setText(update_views + self.tr(" views"))
        self._published_time_label.setText(row_data[ResultFields.VideoPublishedTime])
        self._views_rate_label.setText(self._model.header[ResultFields.ViewRate] + ": " + row_data[ResultFields.ViewRate])
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
        self._chart_combobox.addItem(self.tr("Channels distribution map"))
        self._chart_combobox.addItem(self.tr("Video duration map"))
        self._chart_combobox.currentIndexChanged.connect(self._on_current_chart_changed)
        main_layout.addWidget(self._chart_combobox)

        self._chart_view = QChartView()
        self._chart_view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self._chart_view)

        self._channels_pie_series = ChannelsPieSeries(model)
        self._channels_pie_chart = QChart()
        self._channels_pie_chart.addSeries(self._channels_pie_series)
        self._charts.append(self._channels_pie_chart)

        self._video_duration_chart = VideoDurationChart(model)
        self._charts.append(self._video_duration_chart)

        self._chart_view.setChart(self._channels_pie_chart)

    def set_current_index(self, index: QModelIndex):
        if not self._current_index_following or index is None or index.row() < 0 or index.row() >= len(self._model.result):
            self._channels_pie_series.set_current_channel(None)
            return

        row_data = self._model.result[index.row()]
        self._channels_pie_series.set_current_channel(row_data[ResultFields.ChannelTitle])
        self._video_duration_chart.set_current_index(index)

    def set_current_index_following(self, follow):
        self._current_index_following = follow
        if not follow:
            self.set_current_index(None)

    def set_charts_theme(self, theme):
        self._channels_pie_chart.setTheme(theme)
        self._channels_pie_series.rebuild()

    def _on_current_chart_changed(self, index):
        self._chart_view.setChart(self._charts[index])
