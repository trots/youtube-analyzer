from dataclasses import dataclass
from PySide6.QtCore import (
    QByteArray,
    QSettings
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

    def __init__(self, app_name: str):
        self._impl = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, app_name)

    def get(self, key: SettingsKey):
        return self._impl.value(key.key, key.default_value)

    def set(self, key: SettingsKey, value: any):
        self._impl.setValue(key.key, value)
