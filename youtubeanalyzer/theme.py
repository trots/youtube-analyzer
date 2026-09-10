from PySide6.QtCore import (
    Qt
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QIcon,
    QPainter,
    QPalette,
    QPixmap
)
import PySide6.QtSvg  # to enable svg rendering
from PySide6.QtWidgets import (
    QApplication
)


THEMED_ICON_SIZE: int = 24


def themed_icon(resource_path: str) -> QIcon:
    icon = QIcon()
    icon.addPixmap(_tinted_pixmap(resource_path, QGuiApplication.palette().color(QPalette.ColorRole.ButtonText)),
                   QIcon.Mode.Normal)
    icon.addPixmap(_tinted_pixmap(resource_path, QGuiApplication.palette().color(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText)), QIcon.Mode.Disabled)
    return icon


def _tinted_pixmap(resource_path: str, color: QColor) -> QPixmap:
    source_pixmap = QIcon(resource_path).pixmap(THEMED_ICON_SIZE, THEMED_ICON_SIZE)
    tinted_pixmap = QPixmap(source_pixmap.size())
    tinted_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(tinted_pixmap)
    painter.drawPixmap(0, 0, source_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted_pixmap.rect(), color)
    painter.end()
    return tinted_pixmap


class Theme:
    Light: int = 0
    Dark: int = 1

    @staticmethod
    def is_dark(theme_index: int) -> bool:
        return theme_index == Theme.Dark

    @staticmethod
    def apply(app: QApplication, theme_index: int):
        if Theme.is_dark(theme_index):
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#2b2b2b"))
            palette.setColor(QPalette.WindowText, QColor("#e0e0e0"))
            palette.setColor(QPalette.Base, QColor("#1e1e1e"))
            palette.setColor(QPalette.AlternateBase, QColor("#2b2b2b"))
            palette.setColor(QPalette.ToolTipBase, QColor("#1e1e1e"))
            palette.setColor(QPalette.ToolTipText, QColor("#e0e0e0"))
            palette.setColor(QPalette.Text, QColor("#e0e0e0"))
            palette.setColor(QPalette.Button, QColor("#2b2b2b"))
            palette.setColor(QPalette.ButtonText, QColor("#e0e0e0"))
            palette.setColor(QPalette.BrightText, QColor("#ff5c5c"))
            palette.setColor(QPalette.Link, QColor("#8ab4f8"))
            palette.setColor(QPalette.PlaceholderText, QColor("#9e9e9e"))
            palette.setColor(QPalette.Highlight, QColor("#3d6fb4"))
            palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.Active, QPalette.Button, QColor("#2b2b2b"))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#2b2b2b").lighter())
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#2b2b2b").lighter())
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#2b2b2b").lighter())
            palette.setColor(QPalette.Disabled, QPalette.Light, QColor("#2b2b2b"))
            app.setPalette(palette)
        else:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("#f5f5f5"))
            palette.setColor(QPalette.WindowText, QColor("#202020"))
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.AlternateBase, QColor("#f5f5f5"))
            palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ToolTipText, QColor("#202020"))
            palette.setColor(QPalette.Text, QColor("#202020"))
            palette.setColor(QPalette.Button, QColor("#f5f5f5"))
            palette.setColor(QPalette.ButtonText, QColor("#202020"))
            palette.setColor(QPalette.BrightText, QColor("#d32f2f"))
            palette.setColor(QPalette.Link, QColor("#1a4a8f"))
            palette.setColor(QPalette.Highlight, QColor("#3d6fb4"))
            palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#f5f5f5").darker())
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#f5f5f5").darker())
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#f5f5f5").darker())
            app.setPalette(palette)
