from PySide6.QtCore import (
    QSize,
    Qt,
    QEvent,
    QModelIndex,
    QUrl
)
from PySide6.QtGui import (
    QPixmap
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
    QToolButton,
    QStyle
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    ImageDownloader
)
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel
)
from youtubeanalyzer.widgets import (
    PixmapLabel
)
from youtubeanalyzer.preview_actions_menu import (
    PreviewActionsMenu
)


class VideoDetailsWidget(QWidget):
    def __init__(self, settings: Settings, model: ResultTableModel, parent: QWidget = None):
        super().__init__(parent)
        self._settings: Settings = settings
        self._model: ResultTableModel = model
        self._model.dataChanged.connect(self._on_model_data_changed)
        self._current_index: QModelIndex = None
        self._logo_downloader = ImageDownloader()
        self._logo_downloader.finished.connect(self._on_logo_download_finished)
        self._logo_downloader.error.connect(self._on_download_error)

        self._preview_actions_menu = PreviewActionsMenu(self._settings, PreviewActionsMenu.Actions.All, self)

        spacing = 10
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()

        self._preview_label = PixmapLabel(main_widget)
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._preview_label.customContextMenuRequested.connect(self._show_preview_actions_menu)
        self._preview_label.installEventFilter(self)
        main_layout.addWidget(self._preview_label)

        self._preview_actions_button = QToolButton(self._preview_label)
        self._preview_actions_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self._preview_actions_button.setToolTip(self.tr("Download or copy preview image"))
        self._preview_actions_button.setAutoRaise(True)
        self._preview_actions_button.clicked.connect(self._show_preview_actions_menu_at_button)
        self._preview_actions_button.hide()

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
        self._preview_actions_menu.set_current_video(
            row_data[ResultFields.VideoTitle], self._model.get_video_preview_sizes(index.row()))
        if self._preview_actions_menu.has_sizes():
            self._reposition_preview_actions_button()
            self._preview_actions_button.show()
        else:
            self._preview_actions_button.hide()
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
        self._preview_actions_menu.set_current_video("", [])
        self._preview_actions_button.hide()
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

    def eventFilter(self, obj, event):
        if obj is self._preview_label and event.type() == QEvent.Type.Resize:
            self._reposition_preview_actions_button()
        return super().eventFilter(obj, event)

    def _reposition_preview_actions_button(self):
        margin = 4
        button_size = self._preview_actions_button.sizeHint()
        x = self._preview_label.width() - button_size.width() - margin
        self._preview_actions_button.move(max(0, x), margin)

    def _show_preview_actions_menu(self, pos):
        if self._preview_actions_menu.has_sizes():
            self._preview_actions_menu.exec(self._preview_label.mapToGlobal(pos))

    def _show_preview_actions_menu_at_button(self):
        if self._preview_actions_menu.has_sizes():
            self._preview_actions_menu.exec(
                self._preview_actions_button.mapToGlobal(self._preview_actions_button.rect().bottomLeft()))
