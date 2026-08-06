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
    QCheckBox,
    QTabWidget
)
from youtubeanalyzer.defines import (
    app_name
)
from youtubeanalyzer.engine import (
    SearchAutocompleteDownloader
)
from youtubeanalyzer.settings import (
    Settings,
    SettingsKey
)


def create_link_label(link: str, text: str):
    label = QLabel("<a href=\"" + link + "\">" + text + "</a>")
    label_size_policy = label.sizePolicy()
    label_size_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
    label.setSizePolicy(label_size_policy)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(True)
    return label


def critical_message(parent, text):
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Critical)
    dialog.setWindowTitle(app_name)
    dialog.setText(text)
    return dialog.exec()


def print_exception_chain(exception: BaseException):
    output = ""
    if hasattr(exception, "__cause__") and exception.__cause__:
        output += print_exception_chain(exception.__cause__)
    output += " - " + str(exception)
    if hasattr(exception, "__notes__") and exception.__notes__:
        output += " (" + "; ".join(exception.__notes__) + ")"
    output += "\n"
    return output


def show_detailed_message(severity_icon: QMessageBox.Icon, parent: QWidget, text: str, details: str | BaseException):
    dialog = QMessageBox(parent)
    dialog.setIcon(severity_icon)
    dialog.setWindowTitle(app_name)
    dialog.setText(text)
    if type(details) is str:
        dialog.setDetailedText(details)
    else:
        details_text: str = print_exception_chain(details)
        if details_text:
            details_text = QObject.tr("Causes:") + "\n" + details_text
        dialog.setDetailedText(details_text)
    return dialog.exec()


def critical_detailed_message(parent: QWidget, text: str, details: str | Exception):
    return show_detailed_message(QMessageBox.Icon.Critical, parent, text, details)


def warning_detailed_message(parent: QWidget, text: str, details: str | Exception):
    return show_detailed_message(QMessageBox.Icon.Warning, parent, text, details)


class DontShowAgainWarningDialog(QMessageBox):
    def __init__(self, parent: QWidget, text: str, details: str | BaseException):
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowTitle(app_name)
        self.setText(text)
        if type(details) is str:
            self.setDetailedText(details)
        else:
            details_text: str = print_exception_chain(details)
            if details_text:
                details_text = QObject.tr("Causes:") + "\n" + details_text
            self.setDetailedText(details_text)
        self._check_box = QCheckBox(self.tr("Don't show again"))
        self.setCheckBox(self._check_box)

    def is_dont_show_again(self):
        return 1 if self._check_box.isChecked() else 0


def warning_detailed_message_dont_show_again(parent: QWidget, settings: Settings, settings_key: SettingsKey,
                                             text: str, details: str | BaseException):
    if int(settings.get(settings_key)):
        return
    dialog = DontShowAgainWarningDialog(parent, text, details)
    dialog.exec()
    settings.set(settings_key, dialog.is_dont_show_again())


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
