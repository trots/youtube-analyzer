from typing import Optional
from PySide6.QtCore import (
    QSize,
    QObject,
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
    QMessageBox,
    QTabWidget
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


def critical_detailed_message(parent, title, text, details_text):
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


class FixedTabWidget(QTabWidget):
    """
    A QTabWidget subclass that keeps current tab index across hide/show operations.

    This workaround addresses a Qt framework limitation where QTabWidget resets
    currentIndex() to 0 when hidden.
    """
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._last_visible_index: Optional[int] = None

    def get_last_visible_index(self):
        return self._last_visible_index

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)

        if event.size().width() == 0:
            self._hide_handler()
        else:
            self._show_handler()

    def hideEvent(self, event):
        self._hide_handler()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self._show_handler()

    def _hide_handler(self):
        self._last_visible_index = self.currentIndex()
        self.setCurrentIndex(0)

    def _show_handler(self):
        if self.count() > 0 and self._last_visible_index is not None:
            self.setCurrentIndex(self._last_visible_index)
            self._last_visible_index = None
