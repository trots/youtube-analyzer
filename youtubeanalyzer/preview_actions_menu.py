from typing import Optional
import re
from PySide6.QtCore import (
    QUrl,
    QFileInfo
)
from PySide6.QtGui import (
    QGuiApplication
)
from PySide6.QtWidgets import (
    QWidget,
    QMenu,
    QFileDialog
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    ImageDownloader,
    FileDownloader
)
from youtubeanalyzer.widgets import (
    critical_detailed_message
)


class PreviewActionsMenu(QMenu):
    class Actions:
        Copy: int = 1
        Download: int = 2
        All: int = Copy | Download

    def __init__(self, settings: Settings, actions: int = Actions.All, parent: QWidget = None):
        super().__init__(parent)
        self._settings: Settings = settings
        self._video_title: str = ""
        self._preview_sizes: list[dict] = []
        self._pending_downloads: dict[str, str] = {}  # {url: save file path}

        self._download_submenu: Optional[QMenu] = None
        self._download_downloader: Optional[FileDownloader] = None
        if actions & PreviewActionsMenu.Actions.Download:
            self._download_submenu = self.addMenu(self.tr("Download preview"))
            self._download_downloader = FileDownloader(self)
            self._download_downloader.finished.connect(self._on_file_downloaded)
            self._download_downloader.error.connect(self._on_download_error)

        self._copy_submenu: Optional[QMenu] = None
        self._copy_downloader: Optional[ImageDownloader] = None
        if actions & PreviewActionsMenu.Actions.Copy:
            self._copy_submenu = self.addMenu(self.tr("Copy preview"))
            self._copy_downloader = ImageDownloader(self)
            self._copy_downloader.finished.connect(self._on_image_downloaded)
            self._copy_downloader.error.connect(self._on_copy_error)

    def set_current_video(self, video_title: str, preview_sizes: list[dict]):
        self._video_title = video_title
        self._preview_sizes = preview_sizes or []
        self._rebuild_submenus()

    def has_sizes(self) -> bool:
        return bool(self._preview_sizes)

    def _rebuild_submenus(self):
        # Reuse existing QAction objects instead of clear()+addAction() on every call: tearing down and
        # recreating Qt objects on every row selection was hitting a rare PySide/shiboken object-identity
        # bug when colliding with QNetworkReply objects freed around the same time (deleteLater()).
        if self._download_submenu is not None:
            self._sync_submenu_actions(self._download_submenu, self._download)
        if self._copy_submenu is not None:
            self._sync_submenu_actions(self._copy_submenu, self._copy)

    def _sync_submenu_actions(self, submenu: QMenu, on_size_selected) -> None:
        actions = submenu.actions()
        for i, size in enumerate(self._preview_sizes):
            label = f"{size['width']}×{size['height']}"
            if i < len(actions):
                action = actions[i]
                action.setText(label)
                action.setVisible(True)
                action.triggered.disconnect()
            else:
                action = submenu.addAction(label)
            action.triggered.connect(lambda checked=False, s=size: on_size_selected(s))
        for extra_action in actions[len(self._preview_sizes):]:
            extra_action.setVisible(False)

    def _download(self, size: dict):
        url = size["url"]
        extension = QUrl(url).path().rsplit(".", 1)[-1] if "." in QUrl(url).path() else "jpg"
        default_name = self._sanitize_filename(self._video_title) + "." + extension
        last_save_dir = self._settings.get(Settings.LastPreviewSaveDir)
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save preview image"), last_save_dir + "/" + default_name,
            self.tr("Images") + f" (*.{extension})")
        if not file_path:
            return
        self._settings.set(Settings.LastPreviewSaveDir, QFileInfo(file_path).dir().absolutePath())

        request_url = QUrl(url)
        self._pending_downloads[request_url.toString()] = file_path
        self._download_downloader.start_download(request_url)

    def _on_file_downloaded(self, url: QUrl, data: bytes):
        file_path = self._pending_downloads.pop(url.toString(), None)
        if file_path is None:
            return
        try:
            with open(file_path, "wb") as preview_file:
                preview_file.write(data)
        except OSError as exc:
            critical_detailed_message(self, self.tr("Failed to save preview image"), exc)

    def _on_download_error(self, url: QUrl, error: str):
        if self._pending_downloads.pop(url.toString(), None) is None:
            return
        critical_detailed_message(self, self.tr("Failed to download preview image"), error)

    def _copy(self, size: dict):
        self._copy_downloader.start_download(QUrl(size["url"]))

    def _on_image_downloaded(self, image):
        if not image.isNull():
            QGuiApplication.clipboard().setImage(image)

    def _on_copy_error(self, error: str):
        critical_detailed_message(self, self.tr("Failed to copy preview image"), error)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
        return sanitized or "preview"
