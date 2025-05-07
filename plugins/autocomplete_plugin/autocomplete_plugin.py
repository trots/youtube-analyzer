from PySide6.QtCore import (
    Qt,
    QObject
)
from PySide6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLineEdit,
    QListWidget,
    QStackedLayout,
    QLabel
)
from youtubeanalyzer.plugins import AbstractPlugin
from youtubeanalyzer.settings import (
    Settings,
    StateSaveable
)
from youtubeanalyzer.engine import (
    SearchAutocompleteDownloader
)
from youtubeanalyzer.widgets import (
    TabWorkspaceFactory,
    TabWidget
)


class AutocompleteWorkspace(QWidget, StateSaveable):
    def __init__(self, settings: Settings, parent: QWidget = None):
        super().__init__(parent)
        self._settings = settings
        self._autocomplete_downloader = SearchAutocompleteDownloader()
        self._autocomplete_downloader.finished.connect(self._on_autocomplete_downloaded)

        v_layout = QVBoxLayout()
        request_edit = QLineEdit()
        request_edit.setPlaceholderText(self.tr("Enter request to see autocomplete list..."))
        request_edit.setToolTip(request_edit.placeholderText())
        request_edit.textChanged.connect(self._autocomplete_downloader.start_download_delayed)
        v_layout.addWidget(request_edit)

        tool_panel_layout = QHBoxLayout()
        copy_all_button = QPushButton(self.tr("Copy all"))
        copy_all_button.setEnabled(False)
        copy_all_button.setToolTip(self.tr("Copy the all text of the autocomplete list below"))
        copy_all_button.clicked.connect(self._on_copy_all)
        tool_panel_layout.addWidget(copy_all_button)
        copy_selected_button = QPushButton(self.tr("Copy selected"))
        copy_selected_button.setEnabled(False)
        copy_selected_button.setToolTip(self.tr("Copy text of the selected items of the autocomplete list below"))
        copy_selected_button.clicked.connect(self._on_copy_selected)
        tool_panel_layout.addWidget(copy_selected_button)
        tool_panel_layout.addStretch()
        v_layout.addLayout(tool_panel_layout)

        stacked_layout = QStackedLayout()
        empty_label = QLabel(self.tr("Autocomplete list is empty"))
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stacked_layout.addWidget(empty_label)
        self._autocomplete_list_widget = QListWidget()
        self._autocomplete_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        stacked_layout.addWidget(self._autocomplete_list_widget)
        v_layout.addLayout(stacked_layout)
        stacked_layout.setCurrentIndex(0)
        self._autocomplete_list_widget.model().rowsInserted.connect(
            lambda: stacked_layout.setCurrentIndex(0 if self._autocomplete_list_widget.count() == 0 else 1))
        self._autocomplete_list_widget.model().rowsInserted.connect(
            lambda: copy_all_button.setEnabled(False if self._autocomplete_list_widget.count() == 0 else True))
        self._autocomplete_list_widget.model().rowsInserted.connect(
            lambda: copy_selected_button.setEnabled(False if self._autocomplete_list_widget.count() == 0 else True))
        self._autocomplete_list_widget.model().modelReset.connect(
            lambda: stacked_layout.setCurrentIndex(0 if self._autocomplete_list_widget.count() == 0 else 1))
        self._autocomplete_list_widget.model().modelReset.connect(
            lambda: copy_all_button.setEnabled(False if self._autocomplete_list_widget.count() == 0 else True))
        self._autocomplete_list_widget.model().modelReset.connect(
            lambda: copy_selected_button.setEnabled(False if self._autocomplete_list_widget.count() == 0 else True))

        self.setLayout(v_layout)

    def load_state(self):
        pass  # Not needed

    def save_state(self):
        pass  # Not needed

    def _on_autocomplete_downloaded(self, autocomplete_list):
        self._autocomplete_list_widget.clear()
        self._autocomplete_list_widget.addItems(autocomplete_list)

    def _on_copy_all(self):
        text_to_copy = ""
        for i in range(self._autocomplete_list_widget.count()):
            item = self._autocomplete_list_widget.item(i)
            text_to_copy += item.text() + "\n"
        text_to_copy = text_to_copy[:-1]  # Remove the last \n
        QApplication.clipboard().setText(text_to_copy)

    def _on_copy_selected(self):
        text_to_copy = ""
        for i in range(self._autocomplete_list_widget.count()):
            item = self._autocomplete_list_widget.item(i)
            if item.isSelected():
                text_to_copy += item.text() + "\n"
        text_to_copy = text_to_copy[:-1]  # Remove the last \n
        QApplication.clipboard().setText(text_to_copy)


class AutocompleteWorkspaceFactory(TabWorkspaceFactory):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def get_uid(self):
        return "2d5c4888-89ff-4b55-ac56-5f411338d807"

    def get_workspace_name(self) -> str:
        return self.tr("Search autocomplete")

    def create_workspace_button(self) -> QPushButton:
        button = QPushButton(self.tr("Search autocomplete..."))
        return button

    def create_workspace_widget(self, settings: Settings, parent: QWidget) -> QWidget:
        return AutocompleteWorkspace(settings, parent)


class AutocompletePlugin(AbstractPlugin):
    def get_name(self) -> str:
        return "autocomplete_plugin"

    def get_human_readable_name(self) -> str:
        return QObject.tr("Autocomplete plugin")

    def get_description(self) -> str:
        return QObject.tr("Adds a new tab to work with YouTube search autocomplete")

    def get_version(self) -> str:
        return "1.0"

    def initialize(self):
        TabWidget.add_workspace_factory(AutocompleteWorkspaceFactory())
