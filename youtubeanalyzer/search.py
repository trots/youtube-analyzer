from PySide6.QtCore import (
    Qt
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QWidget,
    QPushButton
)
from youtubeanalyzer.settings import (
    Settings
)
from youtubeanalyzer.engine import (
    YoutubeApiEngine,
    YoutubeGrepEngine
)
from youtubeanalyzer.widgets import (
    critical_message,
    critical_detailed_message,
    warning_detailed_message,
    SearchLineEdit
)
from youtubeanalyzer.workspace import (
    TabWorkspaceFactory
)
from youtubeanalyzer.video_table_workspace import (
    AbstractVideoTableWorkspace
)


class SearchWorkspace(AbstractVideoTableWorkspace):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(settings, parent)
        self.request_text = ""

    def load_state(self):
        super().load_state()
        self._search_line_edit.setFocus()

    def get_data_name(self):
        return self.request_text or "search"

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

        try:
            engine = self._create_engine()
            if engine.search(self.request_text):
                self._on_insert_widgets()
                self._table_view.resizeColumnsToContents()
                if engine.warnings:
                    warning_detailed_message(self, self.tr("Some items were skipped"), "\n".join(engine.warnings))
            else:
                text = self.tr("Error in the searching process")
                if engine.errorReason is not None:
                    text += ": " + engine.errorReason
                critical_detailed_message(self, text, engine.errorDetails)  # TODO: engine exception
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.setDisabled(False)
            critical_message(self, str(e))

        QApplication.restoreOverrideCursor()
        self.setDisabled(False)

    def _create_engine(self):
        request_limit: int = self._get_request_limit()
        api_key: str = self._get_api_key()
        if not api_key:
            return YoutubeGrepEngine(self.model, request_limit)
        else:
            request_page_limit: int = self._get_request_page_limit()
            return YoutubeApiEngine(api_key, self.model, request_limit, request_page_limit)


class SearchWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def get_uid(self) -> str:
        return "cd8288f5-d985-48de-9730-359a010db967"

    def get_workspace_name(self) -> str:
        return self.tr("Search")

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton(self.tr("Search video..."))
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget) -> QWidget:
        return SearchWorkspace(settings, parent)
