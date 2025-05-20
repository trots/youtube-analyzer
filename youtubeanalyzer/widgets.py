from PySide6.QtCore import (
    QSize,
    Qt,
    QTimer,
    QStringListModel
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QResizeEvent
)
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QCompleter,
    QSizePolicy,
    QMessageBox
)
from youtubeanalyzer.engine import (
    SearchAutocompleteDownloader
)


def create_link_label(link: str, text: str):
    label = QLabel("<a href=\"" + link + "\">" + text + "</a>")
    label_size_policy = label.sizePolicy()
    label_size_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
    label.setSizePolicy(label_size_policy)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(True)
    return label


def critial_detailed_message(parent, title, text, details_text):
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setDetailedText(details_text)
    return dialog.exec()


class PixmapLabel(QLabel):
    def __init__(self, parent=None):
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


class SearchLineEdit(QLineEdit):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.setPlaceholderText(self.tr("Enter request and press 'Search'..."))
        self.setToolTip(self.placeholderText())
        self.setClearButtonEnabled(True)
        self.textEdited.connect(self._on_text_changed)
        self.returnPressed.connect(self._on_return_pressed)

        self._autocomplete_model = QStringListModel()
        completer = QCompleter(self._autocomplete_model)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.setCompleter(completer)

        self._autocomplete_downloader = SearchAutocompleteDownloader()
        self._autocomplete_downloader.finished.connect(self._on_autocomplete_downloaded)

    def _on_text_changed(self):
        self._autocomplete_downloader.start_download_delayed(self.text())

    def _on_return_pressed(self):
        popup = self.completer().popup()
        if popup:
            popup.hide()

    def _on_autocomplete_downloaded(self, autocomplete_list):
        self._autocomplete_model.setStringList(autocomplete_list)
