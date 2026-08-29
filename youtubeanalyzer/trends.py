import pycountry
from PySide6.QtCore import (
    Qt,
    QObject,
    QTimer
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QComboBox
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    YoutubeApiEngine
)
from youtubeanalyzer.widgets import (
    critical_message,
    critical_detailed_message,
    warning_detailed_message_dont_show_again
)
from youtubeanalyzer.workspace import (
    TabWorkspaceFactory
)
from youtubeanalyzer.video_table_workspace import (
    AbstractVideoTableWorkspace
)


class TrendsWorkspace(AbstractVideoTableWorkspace):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(settings, parent)

        self._selected_category = None
        self._loaded_category_id = None

        QTimer.singleShot(0, self, self._update_categories)

    def load_state(self):
        super().load_state()
        index = self._region_combo_box.findData(self._settings.get(Settings.TrendsRegion))
        if index >= 0:
            self._region_combo_box.setCurrentIndex(index)
        self._loaded_category_id = int(self._settings.get(Settings.TrendsVideoCategoryId))

    def save_state(self):
        super().save_state()
        self._settings.set(Settings.TrendsRegion, self._region_combo_box.currentData())
        if self._category_combo_box.currentData() is not None:
            self._settings.set(Settings.TrendsVideoCategoryId, int(self._category_combo_box.currentData()))

    def get_data_name(self):
        category = self._category_combo_box.currentText()
        region = self._region_combo_box.currentData()
        return (category + " " + region + " trends") if category and region else ""

    def handle_preferences_change(self):
        super().handle_preferences_change()
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if api_key and self._category_combo_box.count() == 0:
            self._update_categories()

    def _create_toolbar(self, h_layout: QHBoxLayout):
        h_layout.addWidget(QLabel(self.tr("Category:")))
        self._category_combo_box = QComboBox()
        self._category_combo_box.setToolTip(self.tr("Select the video category to search trends"))
        h_layout.addWidget(self._category_combo_box, 1)
        h_layout.addSpacing(10)
        h_layout.addWidget(QLabel(self.tr("Region:")))
        self._region_combo_box = QComboBox()
        self._region_combo_box.setToolTip(self.tr("Select the region to search trends"))
        for country in pycountry.countries:
            self._region_combo_box.addItem(country.name, country.alpha_2)
        self._region_combo_box.setCurrentText("United States")
        h_layout.addWidget(self._region_combo_box)
        self._region_combo_box.currentIndexChanged.connect(self._update_categories)
        h_layout.addStretch(2)

    def _update_categories(self):
        self._category_combo_box.clear()
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            return

        engine = YoutubeApiEngine(api_key)
        region_code = self._region_combo_box.currentData()
        if not region_code:
            region_code = "US"
        categories_lang = "ru_RU" if self._settings.get(Settings.Language) == "Ru" else "en_US"
        categories = engine.get_video_categories(region_code, categories_lang)
        if len(categories) == 0:
            critical_detailed_message(self, self.tr("Unable to get video categories"), engine.errorDetails)
        elif engine.warnings:
            warning_detailed_message_dont_show_again(
                self, self._settings, Settings.DontShowSkippedItemsWarning,
                self.tr("Some video categories were skipped"), "\n".join(engine.warnings))
        self._category_combo_box.addItem(self.tr("All"), 0)
        for category in categories:
            self._category_combo_box.addItem(category.text, category.id)
        if self._loaded_category_id is not None:
            index = self._category_combo_box.findData(self._loaded_category_id)
            if index >= 0:
                self._category_combo_box.setCurrentIndex(index)
            self._loaded_category_id = None

    def _get_history_context(self):
        return (self._category_combo_box.currentData(), self._region_combo_box.currentData())

    def _restore_history_context(self, context):
        if context is None:
            return
        category_id, region_code = context
        region_index = self._region_combo_box.findData(region_code)
        if region_index >= 0:
            self._region_combo_box.setCurrentIndex(region_index)  # synchronously reloads categories for the region
        category_index = self._category_combo_box.findData(category_id)
        if category_index >= 0:
            self._category_combo_box.setCurrentIndex(category_index)

    def _on_search_clicked(self):
        self.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        self.model.clear()
        self._sort_model.sort(-1)
        self._details_widget.clear()
        QApplication.instance().processEvents()

        category_id = self._category_combo_box.currentData()
        if category_id is None:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            critical_message(self, self.tr("Unable to show trends. Video category is not selected."))
            return

        region_code = self._region_combo_box.currentData()
        if not region_code:
            region_code = "US"
            print("Region code is not set. Using 'US' by default")

        try:
            api_key: str = self._get_api_key()
            request_limit: int = self._get_request_limit()
            request_page_limit: int = self._get_request_page_limit()

            engine = YoutubeApiEngine(api_key, self.model, request_limit, request_page_limit)
            if engine.trends(int(category_id), region_code):
                self._on_insert_widgets()
                self._table_view.resizeColumnsToContents()
                if engine.warnings:
                    warning_detailed_message_dont_show_again(
                        self, self._settings, Settings.DontShowSkippedItemsWarning,
                        self.tr("Some items were skipped"), "\n".join(engine.warnings))
                self._push_history()
            else:
                text = self.tr("Trends searching failed")
                if engine.errorReason is not None:
                    text += ": " + engine.errorReason
                critical_detailed_message(self, text, engine.errorDetails)  # TODO: engine exception
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            critical_message(self, str(e))

        QApplication.restoreOverrideCursor()
        self.setDisabled(False)


class TrendsWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def get_uid(self) -> str:
        return "6ae85ee6-2712-430f-92e6-103b30cb4054"

    def get_workspace_name(self) -> str:
        return self.tr("Trends")

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton(self.tr("Search trends..."))
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget):
        return TrendsWorkspace(settings, parent)
