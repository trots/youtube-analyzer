from dataclasses import dataclass
from PySide6.QtCore import (
    QByteArray,
    QSettings
)
from PySide6.QtWidgets import (
    QLineEdit,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QLabel
)

@dataclass
class SettingsKey:
    key: str
    default_value: any

class Settings:
    MainWindowGeometry = SettingsKey("main_window_geometry", QByteArray())
    RequestLimit = SettingsKey("request_limit", 10)
    LastSaveDir = SettingsKey("last_save_dir", "")
    DontAskAgainExit = SettingsKey("dont_ask_again_exit", 0)
    YouTubeApiKey = SettingsKey("youtube_api_key", "")

    def __init__(self, app_name: str):
        self._impl = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, app_name)

    def get(self, key: SettingsKey):
        return self._impl.value(key.key, key.default_value)

    def set(self, key: SettingsKey, value: any):
        self._impl.setValue(key.key, value)


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent = None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        yt_api_key_label = QLabel("YouTube API Key:")
        layout.addWidget(yt_api_key_label)
        self._yt_api_key_edit = QLineEdit(self._settings.get(Settings.YouTubeApiKey))
        self._yt_api_key_edit.setToolTip("Set the key to use the YouTube API for YouTube search")
        layout.addWidget(self._yt_api_key_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accepted)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _on_accepted(self):
        self._settings.set(Settings.YouTubeApiKey, self._yt_api_key_edit.text())
        self.accept()
