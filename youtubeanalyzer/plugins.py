import sys
import importlib
import pkgutil
from pathlib import Path
from PySide6.QtWidgets import QWidget


class AbstractPlugin:
    def get_name(self) -> str:
        pass

    def get_human_readable_name(self) -> str:
        pass

    def get_description(self) -> str:
        pass

    def get_version(self) -> str:
        pass

    def initialize(self, parent: QWidget):
        pass

    def execute(self):
        pass


class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self._plugin_dir: str = plugin_dir
        self._plugins: list[AbstractPlugin] = []

    def load_plugins(self):
        is_compiled_executable = getattr(sys, "frozen", False)
        if is_compiled_executable:  # For exe
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent

        plugin_path = base_dir / self._plugin_dir

        if not plugin_path.exists():
            print(f"Warning: {plugin_path} is not found!")
            return

        for _, name, _ in pkgutil.iter_modules([str(plugin_path)]):
            if is_compiled_executable:
                module = importlib.import_module(f"{self._plugin_dir}.{name}")
            else:
                module = importlib.import_module(f"{self._plugin_dir}.{name}.{name}")
            for item in dir(module):
                obj = getattr(module, item)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, AbstractPlugin)
                    and obj != AbstractPlugin
                ):
                    self._plugins.append(obj())

    def get_plugins(self):
        return self._plugins
