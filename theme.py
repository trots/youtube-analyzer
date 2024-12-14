from PySide6.QtCore import (
    Qt
)
from PySide6.QtGui import (
    QColor,
    QPalette
)
from PySide6.QtWidgets import (
    QApplication
)


class Theme:
    System: int = 0
    Dark: int = 1

    @staticmethod
    def apply(app: QApplication, theme_index: int):
        if theme_index == Theme.Dark:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.black)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(148, 192, 236))
            palette.setColor(QPalette.Highlight, QColor(19, 60, 110))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(53, 53, 53).lighter())
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(53, 53, 53).lighter())
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(53, 53, 53).lighter())
            palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53))
            app.setPalette(palette)
        else:
            palette = QPalette()
            palette.setColor(QPalette.Link, QColor(19, 60, 110))
            app.setPalette(palette)
