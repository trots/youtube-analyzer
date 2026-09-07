from PySide6.QtCore import (
    Signal,
    QObject
)


class QSingleton(type(QObject)):
    """Metaclass for Qt classes that are singletons."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance = None

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance


class EventBus(QObject, metaclass=QSingleton):
    create_new_tab = Signal(str, object)  # workspace_uid, workspace_data
    quit_requested = Signal()
    workspace_created = Signal(object)  # workspace
    results_updated = Signal()  # emitted when a workspace's results data has changed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
