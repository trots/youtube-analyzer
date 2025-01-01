from PySide6.QtCore import (
    Qt
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QWidget,
    QPushButton
)
from youtubeanalyzer.defines import (
    app_name
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    YoutubeApiEngine,
    YoutubeGrepEngine
)
from youtubeanalyzer.model import (
    ResultFields
)
from youtubeanalyzer.widgets import (
    critial_detailed_message,
    create_link_label,
    SearchLineEdit,
    TabWorkspaceFactory,
    AbstractVideoTableWorkspace
)


class SearchWorkspace(AbstractVideoTableWorkspace):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(settings, parent)
        self.request_text = ""

    def load_state(self):
        super().load_state()
        self._search_line_edit.setFocus()

    def _create_toolbar(self, h_layout: QHBoxLayout):
        self._search_line_edit = SearchLineEdit()
        self._search_line_edit.returnPressed.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_line_edit)

    def _on_search_clicked(self):
        self.request_text = self._search_line_edit.text()

        if self.request_text == "":
            return

        self.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        self.model.clear()
        self._sort_model.sort(-1)
        self._details_widget.clear()
        QApplication.instance().processEvents()

        engine = self._create_engine()
        if engine.search(self.request_text):
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
            text = self.tr("Error in the searching process")
            if engine.errorReason is not None:
                text += ": " + engine.errorReason
            critial_detailed_message(self, app_name, text, engine.errorDetails)

        QApplication.restoreOverrideCursor()
        self.setDisabled(False)

    def _create_engine(self):
        request_limit = self._search_limit_spin_box.value()
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            return YoutubeGrepEngine(self.model, request_limit)
        else:
            return YoutubeApiEngine(api_key, self.model, request_limit)


class SearchWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def get_workspace_name(self) -> str:
        return self.tr("Search")

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton(self.tr("Search video..."))
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget) -> QWidget:
        return SearchWorkspace(settings, parent)
