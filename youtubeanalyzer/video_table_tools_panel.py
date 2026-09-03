from PySide6.QtCore import (
    Signal,
    Qt
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedLayout,
    QPushButton,
    QFrame,
    QButtonGroup,
    QRadioButton,
    QSlider
)
from youtubeanalyzer.settings import (
    Settings,
    StateSaveable
)
from youtubeanalyzer.model import (
    ResultTableModel
)
from youtubeanalyzer.filters import (
    ResultSortFilterProxyModel
)


class VideoTableToolsPanel(StateSaveable, QWidget):
    def __init__(self, settings: Settings, parent: QWidget = None):
        StateSaveable.__init__(self, settings)
        QWidget.__init__(self, parent)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._header_layout: QHBoxLayout = QHBoxLayout()
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.addStretch()
        main_layout.addLayout(self._header_layout)

        self._panel_widget: QFrame = QFrame()
        self._panel_widget.setFrameShape(QFrame.Shape.StyledPanel)
        self._panel_widget.setLayout(QStackedLayout())
        self._panel_widget.setVisible(False)
        main_layout.addWidget(self._panel_widget)

        self._header_button_group: QButtonGroup = QButtonGroup()
        self._header_button_group.setExclusive(True)
        self._header_button_group.buttonClicked.connect(self._on_header_button_clicked)
        self._checked_button: QPushButton = None

    def add_tool_panel(self, name: str, on_tool_tip: str, off_tooltip: str, panel: QWidget):
        panel_layout: QStackedLayout = self._panel_widget.layout()
        new_tab_index: int = panel_layout.count()

        button: QPushButton = QPushButton(name)
        button.setCheckable(True)
        button.setChecked(False)
        button.toggled.connect(lambda checked:
                               button.setToolTip(on_tool_tip) if checked else button.setToolTip(off_tooltip))
        self._header_button_group.addButton(button, new_tab_index)
        self._header_layout.insertWidget(self._header_layout.count() - 1, button)

        panel_layout.addWidget(panel)

    def load_state(self):
        active_panel_index: int = int(self._settings.get(Settings.ActiveToolPanelIndex))
        button_to_check: QPushButton = self._header_button_group.button(active_panel_index)
        if button_to_check:
            button_to_check.setChecked(True)
            self._on_header_button_clicked(button_to_check)
        panel_widget: StateSaveable
        for panel_widget in self._panel_widget.findChildren(StateSaveable, options=Qt.FindChildOption.FindDirectChildrenOnly):
            panel_widget.load_state()

    def save_state(self):
        active_panel_index: int = self._header_button_group.checkedId()
        self._settings.set(Settings.ActiveToolPanelIndex, active_panel_index)
        panel_widget: StateSaveable
        for panel_widget in self._panel_widget.findChildren(StateSaveable, options=Qt.FindChildOption.FindDirectChildrenOnly):
            panel_widget.save_state()

    def _on_header_button_clicked(self, button: QPushButton):
        if self._checked_button and self._checked_button == button:
            self._header_button_group.setExclusive(False)
            button.setChecked(False)
            self._header_button_group.setExclusive(True)
            self._checked_button = None
            self._panel_widget.setVisible(False)
        else:
            view_index: int = self._header_button_group.id(button)
            panel_layout: QStackedLayout = self._panel_widget.layout()
            panel_layout.setCurrentIndex(view_index)
            self._panel_widget.setVisible(True)
            self._checked_button = button


class ViewPanel(StateSaveable, QWidget):
    mode_changed = Signal(ResultTableModel.Mode)
    scale_changed = Signal(float)

    def __init__(self, settings: Settings, model: ResultSortFilterProxyModel, parent=None):
        StateSaveable.__init__(self, settings)
        QWidget.__init__(self, parent)

        main_layout: QHBoxLayout = QHBoxLayout()
        self._extra_stacked_layout: QStackedLayout = QStackedLayout()
        self._extra_stacked_layout.setContentsMargins(0, 0, 0, 0)

        self._table_view_radio: QRadioButton = QRadioButton(self.tr("Table"))
        self._table_view_radio.setChecked(True)
        self._table_view_radio.toggled.connect(lambda: self._on_view_mode_button_clicked(ResultTableModel.Mode.Normal))
        main_layout.addWidget(self._table_view_radio)
        self._extra_stacked_layout.addWidget(QWidget())

        self._gallery_view_radio = QRadioButton(self.tr("Gallery"))
        self._gallery_view_radio.toggled.connect(lambda: self._on_view_mode_button_clicked(ResultTableModel.Mode.Image))
        main_layout.addWidget(self._gallery_view_radio)
        gallery_extra_tools: QWidget = QWidget()
        gallery_extra_tools.setLayout(QHBoxLayout())
        gallery_extra_tools.layout().addWidget(QLabel(self.tr("Scale:")))
        self._scale_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setToolTip(self.tr("Change scale of gallery images"))
        self._scale_slider.setMinimum(50)
        self._scale_slider.setMaximum(250)
        self._scale_slider.setValue(100)
        self._scale_slider.valueChanged.connect(lambda: self.scale_changed.emit(self._get_scale_value()))
        gallery_extra_tools.layout().addWidget(self._scale_slider)
        self._extra_stacked_layout.addWidget(gallery_extra_tools)

        self._extra_stacked_layout.setCurrentIndex(0)
        main_layout.addLayout(self._extra_stacked_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_state(self):
        if int(self._settings.get(Settings.VideoTableMode)) == ResultTableModel.Mode.Image:
            self._gallery_view_radio.setChecked(True)
        else:
            self._table_view_radio.setChecked(True)
        self._scale_slider.setValue(int(self._settings.get(Settings.PreviewScaleIndex)))

    def save_state(self):
        if self._gallery_view_radio.isChecked():
            self._settings.set(Settings.VideoTableMode, ResultTableModel.Mode.Image)
        else:
            self._settings.set(Settings.VideoTableMode, ResultTableModel.Mode.Normal)
        self._settings.set(Settings.PreviewScaleIndex, self._scale_slider.value())

    def _get_scale_value(self):
        return self._scale_slider.value() / 100

    def _on_view_mode_button_clicked(self, mode: ResultTableModel.Mode):
        self._extra_stacked_layout.setCurrentIndex(mode)
        self.mode_changed.emit(mode)
