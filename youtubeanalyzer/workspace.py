from PySide6.QtCore import (
    QObject
)
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QStackedLayout,
    QPushButton,
    QTabWidget
)
from youtubeanalyzer.settings import (
    Settings,
    StateSaveable
)


class WorkspaceWidget(StateSaveable, QWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        StateSaveable.__init__(self, settings)
        QWidget.__init__(self, parent)

    def has_data_to_export(self):
        return False


class TabWorkspaceFactory(QObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def get_uid(self) -> str:
        raise "Not implemented"

    def get_workspace_name(self) -> str:
        raise "Not implemented"

    def create_workspace_button(self) -> QPushButton:
        raise "Not implemented"

    def create_workspace_widget(self, settings, parent) -> WorkspaceWidget:
        raise "Not implemented"


class WorkspaceTab(StateSaveable, QWidget):
    workspace_factories: dict[str, TabWorkspaceFactory] = {}

    @staticmethod
    def add_workspace_factory(factory: TabWorkspaceFactory):
        WorkspaceTab.workspace_factories[factory.get_uid()] = factory

    def __init__(self, settings: Settings, parent_tab_widget: QTabWidget, parent: QWidget = None):
        StateSaveable.__init__(self, settings)
        QWidget.__init__(self, parent)

        self._parent_tab_widget = parent_tab_widget
        self._current_workspace_uid = None

        self._main_stacked_layout = QStackedLayout()

        self._main_layout = QGridLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setLayout(self._main_layout)
        self._main_stacked_layout.addWidget(container)
        self._main_stacked_layout.setCurrentIndex(0)
        self.setLayout(self._main_stacked_layout)

        row = 1
        for uid, factory in WorkspaceTab.workspace_factories.items():
            workspace_button = factory.create_workspace_button()
            workspace_button.clicked.connect(lambda state=None, uid=uid: self.create_workspace(uid))
            self._main_layout.addWidget(workspace_button, row, 1)
            row = row + 1

        self._main_layout.setRowStretch(0, 1)
        self._main_layout.setRowStretch(row, 1)
        self._main_layout.setColumnStretch(0, 1)
        self._main_layout.setColumnStretch(2, 1)

    def current_workspace(self):
        return self._main_stacked_layout.currentWidget() if self._main_stacked_layout.currentIndex() == 1 else None

    def load_state(self):
        workspace_uid = self._settings.get(Settings.TabWorkspaceUid)
        if workspace_uid:
            workspace_widget = self.create_workspace(workspace_uid)
            if workspace_widget:
                workspace_widget.load_state()

    def save_state(self):
        self._settings.set(Settings.TabWorkspaceUid, self._current_workspace_uid)
        if self._current_workspace_uid:
            workspace_widget = self._main_stacked_layout.currentWidget()
            workspace_widget.save_state()

    def handle_preferences_change(self):
        workspace = self.current_workspace()
        if workspace:
            workspace.handle_preferences_change()

    def create_workspace(self, workspace_uid: str):
        if workspace_uid not in WorkspaceTab.workspace_factories:
            return None
        factory = WorkspaceTab.workspace_factories[workspace_uid]
        workspace_widget = factory.create_workspace_widget(self._settings, self)
        self._main_stacked_layout.addWidget(workspace_widget)
        self._main_stacked_layout.setCurrentIndex(1)
        tab_index = self._parent_tab_widget.indexOf(self)
        self._parent_tab_widget.setTabText(tab_index, factory.get_workspace_name())
        self._current_workspace_uid = workspace_uid
        return workspace_widget

    def _create_workspace(self):
        workspace_button = self.sender()
        workspace_index = self._main_layout.indexOf(workspace_button) - 1
        self.create_workspace(workspace_index)
