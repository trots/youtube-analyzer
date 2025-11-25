import sys
import importlib
import pkgutil
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QObject,
    QModelIndex
)
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QTextEdit,
    QMessageBox,
    QFormLayout
)

from youtubeanalyzer.settings import (
    Settings
)


class AbstractPlugin(QObject):
    def get_name(self) -> str:
        pass

    def get_human_readable_name(self) -> str:
        pass

    def get_description(self) -> str:
        pass

    def get_version(self) -> str:
        pass

    def get_license_name(self) -> str:
        pass

    def get_license_text(self) -> str:
        pass

    def get_dependencies(self) -> list[str]:
        return []

    def initialize(self, settings: Settings):
        pass

    def execute(self):
        pass


class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self._plugin_dir: str = plugin_dir
        self._plugins: list[AbstractPlugin] = []

    def load_plugins(self):
        base_dir: Path = self._get_base_dir()
        plugin_path: Path = base_dir / self._plugin_dir

        if not plugin_path.exists():
            print(f"Warning: {plugin_path} is not found!")
            return

        discovered_plugins: dict[str, AbstractPlugin] = self._discover_plugins(plugin_path)
        self._plugins = self._resolve_dependencies(discovered_plugins)

    def initialize_plugins(self, settings: Settings):
        for plugin in self._plugins:
            plugin.initialize(settings)

    def get_plugins(self):
        return self._plugins

    def get_license_text(self, license_name: str):
        if not license_name:
            return ""

        base_dir: Path = self._get_base_dir()
        license_file: Path = base_dir / license_name
        if license_file.exists() and license_file.is_file():
            try:
                return license_file.read_text()
            except Exception:
                print("Read license file exception")
                return ""
        return ""

    def _get_base_dir(self):
        is_compiled_executable = getattr(sys, "frozen", False)
        if is_compiled_executable:  # For exe
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent.parent

    def _discover_plugins(self, plugin_path: Path) -> dict[str, AbstractPlugin]:
        discovered_plugins: dict[str, AbstractPlugin] = {}
        is_compiled_executable: bool = getattr(sys, "frozen", False)

        for _, name, _ in pkgutil.iter_modules([str(plugin_path)]):
            try:
                if is_compiled_executable:
                    module_path: str = f"{self._plugin_dir}.{name}"
                else:
                    module_path: str = f"{self._plugin_dir}.{name}.{name}"

                module = importlib.import_module(module_path)

                for item in dir(module):
                    obj = getattr(module, item)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, AbstractPlugin)
                        and obj != AbstractPlugin
                    ):
                        instance = obj()
                        plugin_name: str = instance.get_name()
                        if plugin_name in discovered_plugins:
                            print(f"Warning: Duplicate plugin name '{plugin_name}' ignored.")
                        else:
                            discovered_plugins[plugin_name] = instance
            except Exception as e:
                print(f"Error loading module {name}: {e}")

        return discovered_plugins

    def _resolve_dependencies(self, discovered_plugins: dict[str, AbstractPlugin]) -> list[AbstractPlugin]:
        sorted_plugins: list[AbstractPlugin] = []
        pending_plugins = discovered_plugins.copy()

        while True:
            added_on_this_pass = []

            for name, plugin in pending_plugins.items():
                dependencies = plugin.get_dependencies()

                dependencies_met: bool = True
                for dep_name in dependencies:
                    if not any(plugin.get_name() == dep_name for plugin in sorted_plugins):
                        dependencies_met = False
                        break

                if dependencies_met:
                    sorted_plugins.append(plugin)
                    added_on_this_pass.append(name)

            if not added_on_this_pass:
                break

            for name in added_on_this_pass:
                del pending_plugins[name]

        if pending_plugins:
            skipped_names = list(pending_plugins.keys())
            print(f"Plugins skipped due to missing or circular dependencies: {skipped_names}")

        return sorted_plugins


class PluginDetailsDialog(QDialog):
    def __init__(self, plugin: AbstractPlugin, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self._plugin: AbstractPlugin = plugin
        self._plugin_manager: PluginManager = plugin_manager

        self.setWindowTitle(self.tr("Plugin Details"))
        self.setModal(True)
        self.setMinimumSize(600, 500)

        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        layout: QVBoxLayout = QVBoxLayout()

        form_layout: QFormLayout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        self._name_label: QLabel = QLabel()
        form_layout.addRow(self.tr("Name:"), self._name_label)

        self._version_label: QLabel = QLabel()
        form_layout.addRow(self.tr("Version:"), self._version_label)

        self._description_text: QTextEdit = QTextEdit()
        self._description_text.setReadOnly(True)
        self._description_text.setMaximumHeight(80)
        form_layout.addRow(self.tr("Description:"), self._description_text)

        layout.addLayout(form_layout)

        self._license_text_edit: QTextEdit = QTextEdit()
        self._license_text_edit.setReadOnly(True)
        form_layout.addRow(self.tr("License:"), self._license_text_edit)

        close_button: QPushButton = QPushButton(self.tr("Close"))
        close_button.clicked.connect(self.accept)
        button_layout: QHBoxLayout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _populate_data(self):
        self._name_label.setText(self._plugin.get_human_readable_name())
        self._version_label.setText(self._plugin.get_version())
        self._description_text.setPlainText(self._plugin.get_description())

        license_name: str = self._plugin.get_license_name()

        if license_name:
            license_text: str = self._plugin_manager.get_license_text(license_name)
            self._license_text_edit.setPlainText(license_text)
        else:
            self._license_text_edit.setPlainText(self.tr("No license text available"))


class AboutPluginsDialog(QDialog):
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self._plugin_manager: PluginManager = plugin_manager
        self.setWindowTitle(self.tr("Installed plugins"))

        layout: QVBoxLayout = QVBoxLayout()
        plugins: list[AbstractPlugin] = self._plugin_manager.get_plugins()
        self._plugins_table: QTableWidget = QTableWidget()
        self._plugins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._plugins_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._plugins_table.setRowCount(len(plugins))
        self._plugins_table.setColumnCount(3)
        self._plugins_table.verticalHeader().setVisible(False)
        self._plugins_table.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Version"), self.tr("Description")])
        self._plugins_table.horizontalHeader().setStretchLastSection(True)

        for row in range(len(plugins)):
            plugin: AbstractPlugin = plugins[row]
            self._plugins_table.setItem(row, 0, QTableWidgetItem(plugin.get_human_readable_name()))
            self._plugins_table.setItem(row, 1, QTableWidgetItem(plugin.get_version()))
            self._plugins_table.setItem(row, 2, QTableWidgetItem(plugin.get_description()))

        self._plugins_table.resizeColumnsToContents()
        layout.addWidget(self._plugins_table)

        details_button: QPushButton = QPushButton(self.tr("Details..."))
        details_button.setToolTip(self.tr("More info about the selected plugin"))
        details_button.clicked.connect(self._on_details_clicked)
        layout.addWidget(details_button, 0, Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def _on_details_clicked(self):
        selected_rows: list[QModelIndex] = self._plugins_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(self, self.tr("No Selection"), self.tr("Please select a plugin to view details."))
            return

        selected_row: int = selected_rows[0].row()
        plugins: list[AbstractPlugin] = self._plugin_manager.get_plugins()

        if 0 <= selected_row < len(plugins):
            plugin: AbstractPlugin = plugins[selected_row]
            details_dialog = PluginDetailsDialog(plugin, self._plugin_manager, self)
            details_dialog.exec()
