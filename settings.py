from dataclasses import dataclass
from PySide2.QtCore import (
    QByteArray,
    QSettings
)
from PySide2.QtWidgets import (
    QLineEdit,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QComboBox,
    QMessageBox
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
    Language = SettingsKey("language", "")
    Theme = SettingsKey("theme", 0)
    MainSplitterState = SettingsKey("main_splitter_state", [0, 0])
    DetailsVisible = SettingsKey("details", True)

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
        self._need_restart = False
        self.setWindowTitle(self.tr("Settings"))
        layout = QVBoxLayout()

        yt_api_key_label = QLabel(self.tr("YouTube API Key:"))
        layout.addWidget(yt_api_key_label)
        self._yt_api_key_edit = QLineEdit(self._settings.get(Settings.YouTubeApiKey))
        self._yt_api_key_edit.setToolTip(self.tr("Set the key to use the YouTube API for YouTube search"))
        layout.addWidget(self._yt_api_key_edit)

        language_label = QLabel(self.tr("Language:"))
        layout.addWidget(language_label)
        self._language_combo = QComboBox()
        self._language_combo.setToolTip(self.tr("Set the interface language"))
        self._language_combo.addItem("English")
        self._language_combo.addItem("Русский")
        if self._settings.get(Settings.Language) == "Ru":
            self._language_combo.setCurrentIndex(1)
        else:
            self._language_combo.setCurrentIndex(0)
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self._language_combo)

        theme_label = QLabel(self.tr("Theme:"))
        layout.addWidget(theme_label)
        self._theme_combo = QComboBox()
        self._theme_combo.setToolTip(self.tr("Set the interface color theme"))
        self._theme_combo.addItem(self.tr("System"))
        self._theme_combo.addItem(self.tr("Dark"))
        self._theme_combo.setCurrentIndex(int(self._settings.get(Settings.Theme)))
        layout.addWidget(self._theme_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accepted)
        button_box.rejected.connect(self._on_rejected)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def is_need_restart(self):
        return self._need_restart

    def _on_accepted(self):
        self._settings.set(Settings.YouTubeApiKey, self._yt_api_key_edit.text())
        if self._language_combo.currentText() == "Русский":
            self._settings.set(Settings.Language, "Ru")
        else:
            self._settings.set(Settings.Language, "En")
        self._settings.set(Settings.Theme, self._theme_combo.currentIndex())

        if self._need_restart:
            text = self.tr("Restart the application now to apply the selected language?")
            if QMessageBox.question(self, self.windowTitle(), text) == QMessageBox.StandardButton.No:
                self._need_restart = False

        self.accept()

    def _on_rejected(self):
        self._need_restart = False
        self.reject()

    def _on_language_changed(self):
        self._need_restart = True
