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
    quitRequested = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def emitQuitRequested(self):
        self.quitRequested.emit()
