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
    QComboBox,
    QMessageBox
)
from youtubeanalyzer.defines import (
    app_name
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    YoutubeApiEngine
)
from youtubeanalyzer.model import (
    ResultFields
)
from youtubeanalyzer.widgets import (
    create_link_label,
    critial_detailed_message,
    TabWorkspaceFactory,
    AbstractVideoTableWorkspace
)


class TrendsWorkspace(AbstractVideoTableWorkspace):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(settings, parent)
        self._search_limit_spin_box.setMaximum(200)

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
        if self._category_combo_box.currentData():
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
            critial_detailed_message(self, app_name, self.tr("Unable to get video categories"), engine.errorDetails)
        for category in categories:
            self._category_combo_box.addItem(category.text, category.id)
        if self._loaded_category_id is not None:
            index = self._category_combo_box.findData(self._loaded_category_id)
            if index >= 0:
                self._category_combo_box.setCurrentIndex(index)
            self._loaded_category_id = None

    def _on_search_clicked(self):
        self.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        self.model.clear()
        self._sort_model.sort(-1)
        self._details_widget.clear()
        QApplication.instance().processEvents()

        category_id = self._category_combo_box.currentData()
        if not category_id:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            QMessageBox.critical(self, app_name, self.tr("Unable to show trends. Video category is not selected."))
            return

        region_code = self._region_combo_box.currentData()
        if not region_code:
            region_code = "US"
            print("Region code is not set. Using 'US' by default")

        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            QMessageBox.critical(self, app_name, self.tr("Unable to show trends. YouTube API key is not set. \
                                                         Please set it in the preferences"))
            return

        request_limit = self._search_limit_spin_box.value()
        if not request_limit:
            request_limit = 10
            print("Request limit is not set. Using '10' by default")

        request_page_limit = int(self._settings.get(Settings.RequestPageLimit))
        if not request_page_limit:
            request_page_limit = 25
            print("Request page limit is not set. Using '25' by default")

        engine = YoutubeApiEngine(api_key, self.model, request_limit, request_page_limit)
        if engine.trends(int(category_id), region_code):
            for i in range(len(self.model.result)):
                video_idx = self._sort_model.index(i, self.model.get_field_column(ResultFields.VideoTitle))
                video_item = self.model.result[i]
                video_label = create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label)

                channel_idx = self._sort_model.index(i, self.model.get_field_column(ResultFields.ChannelTitle))
                channel_label = create_link_label(video_item[ResultFields.ChannelLink], video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label)

            self._table_view.resizeColumnsToContents()
        else:
            text = self.tr("Trends searching failed")
            if engine.errorReason is not None:
                text += ": " + engine.errorReason
            critial_detailed_message(self, app_name, text, engine.errorDetails)

        QApplication.restoreOverrideCursor()
        self.setDisabled(False)


class TrendsWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def get_workspace_name(self) -> str:
        return self.tr("Trends")

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton(self.tr("Search trends..."))
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget) -> QWidget:
        return TrendsWorkspace(settings, parent)
