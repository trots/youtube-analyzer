import sys
import traceback

from PySide6.QtCore import (
    Qt,
    QFileInfo,
    QTranslator,
    QLibraryInfo,
    QKeyCombination
)
from PySide6.QtGui import (
    QIcon,
    QShowEvent,
    QShortcut
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QDialog,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QMessageBox,
    QCheckBox,
    QTextEdit,
    QTabWidget,
    QToolButton,
    QTableWidget,
    QTableWidgetItem
)
from youtubeanalyzer.defines import (
    app_name,
    version
)
from youtubeanalyzer.theme import (
    Theme
)
from youtubeanalyzer.settings import (
    Settings,
    StateSaveable,
    SettingsDialog
)
from youtubeanalyzer.widgets import (
    TabWidget
)
from youtubeanalyzer.search import (
    SearchWorkspaceFactory
)
from youtubeanalyzer.trends import (
    TrendsWorkspaceFactory
)
from youtubeanalyzer.export import (
    export_to_xlsx,
    export_to_csv,
    export_to_html
)
from youtubeanalyzer.plugins import (
    PluginManager
)


app_need_restart = False


class DontAskAgainQuestionDialog(QMessageBox):
    def __init__(self, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(text)
        self.setIcon(QMessageBox.Icon.Question)
        self.addButton(QMessageBox.StandardButton.Yes)
        self.addButton(QMessageBox.StandardButton.No)
        self.setDefaultButton(QMessageBox.StandardButton.No)
        self._check_box = QCheckBox(self.tr("Don't ask again"))
        self.setCheckBox(self._check_box)

    def is_dont_ask_again(self):
        return 1 if self._check_box.isChecked() else 0


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About"))
        layout = QGridLayout()
        layout.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)

        row = 0
        title = QLabel(app_name)
        title.setStyleSheet("font-size: 14px")
        layout.addWidget(title, row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel(self.tr("Software for analyzing of YouTube search output")), row, 0, 1, 2,
                         Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel(self.tr("Version: ") + version),
                         row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel(
            self.tr("Based on: PySide6, youtube-search-python,\n google-api-python-client, XlsxWriter, isodate.")),
            row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        row += 1
        vertical_spacer = QSpacerItem(1, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vertical_spacer, row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        row += 1
        layout.addWidget(QLabel(self.tr("Web site:")), row, 0, Qt.AlignmentFlag.AlignRight)
        site = QLabel("<a href=\"https://github.com/trots/youtube-analyzer\">https://github.com/trots/youtube-analyzer</a>")
        site.setOpenExternalLinks(True)
        layout.addWidget(site, row, 1)
        row += 1
        layout.addWidget(QLabel(self.tr("License:")), row, 0, Qt.AlignmentFlag.AlignRight)
        lic = QLabel("<a href=\"https://github.com/trots/youtube-analyzer/blob/master/LICENSE\">MIT License</a>")
        lic.setOpenExternalLinks(True)
        layout.addWidget(lic, row, 1)

        row += 1
        vertical_spacer = QSpacerItem(1, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vertical_spacer, row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        row += 1
        layout.addWidget(QLabel("Copyright 2023-2024 Alexander Trotsenko"), row, 0, 1, 2,
                         Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel(self.tr("All rights reserved")), row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)


class AuthorsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Authors"))
        layout = QGridLayout()
        layout.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)

        self._edit_text = QTextEdit()
        self._edit_text.setReadOnly(True)
        self._edit_text.append(self.tr("The YouTube Analyzer team, in alphabetical order:\n"))
        self._edit_text.append("Alexander Trotsenko")
        self._edit_text.append("Igor Trofimov")
        self._edit_text.append("Nataliia Trotsenko")

        layout.addWidget(self._edit_text, 0, 0, 1, 2,
                         Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)


class AboutPluginsDialog(QDialog):
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Installed plugins"))
        layout = QVBoxLayout()

        plugins = plugin_manager.get_plugins()
        plugins_table = QTableWidget()
        plugins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        plugins_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        plugins_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        plugins_table.setRowCount(len(plugins))
        plugins_table.setColumnCount(3)
        plugins_table.verticalHeader().setVisible(False)
        plugins_table.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Version"), self.tr("Description")])
        plugins_table.horizontalHeader().setStretchLastSection(True)

        for row in range(len(plugins)):
            plugin = plugins[row]
            plugins_table.setItem(row, 0, QTableWidgetItem(plugin.get_human_readable_name()))
            plugins_table.setItem(row, 1, QTableWidgetItem(plugin.get_version()))
            plugins_table.setItem(row, 2, QTableWidgetItem(plugin.get_description()))

        plugins_table.resizeColumnsToContents()
        layout.addWidget(plugins_table)

        self.setLayout(layout)


class MainWindow(QMainWindow, StateSaveable):
    def __init__(self, settings: Settings):
        super().__init__()

        self._settings = settings
        self._restore_geometry_on_show = True

        self.setWindowTitle(app_name + " " + version)

        file_menu = self.menuBar().addMenu(self.tr("File"))
        export_xlsx_action = file_menu.addAction(self.tr("Export to XLSX..."))
        export_xlsx_action.triggered.connect(self._on_export_xlsx)
        export_csv_action = file_menu.addAction(self.tr("Export to CSV..."))
        export_csv_action.triggered.connect(self._on_export_csv)
        export_html_action = file_menu.addAction(self.tr("Export to HTML..."))
        export_html_action.triggered.connect(self._on_export_html)

        file_menu.addSeparator()
        exit_action = file_menu.addAction(self.tr("Exit"))
        exit_action.setShortcut(QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_Q))
        exit_action.triggered.connect(self.close)

        edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        preferences_action = edit_menu.addAction(self.tr("Preferences..."))
        preferences_action.triggered.connect(self._on_preferences)

        window_menu = self.menuBar().addMenu(self.tr("Window"))
        add_new_tab_action = window_menu.addAction(self.tr("Create a new tab"))
        add_new_tab_action.setShortcut(QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_N))
        add_new_tab_action.triggered.connect(self._create_new_tab)

        help_menu = self.menuBar().addMenu(self.tr("Help"))
        authors_action = help_menu.addAction(self.tr("Authors..."))
        authors_action.triggered.connect(self._on_authors)
        help_menu.addSeparator()
        about_plugins_action = help_menu.addAction(self.tr("About plugins..."))
        about_plugins_action.triggered.connect(self._on_about_plugins)
        about_action = help_menu.addAction(self.tr("About..."))
        about_action.triggered.connect(self._on_about)

        v_layout = QVBoxLayout()

        self._main_tab_widget = QTabWidget()
        self._main_tab_widget.setMovable(True)
        self._main_tab_widget.setTabsClosable(True)
        self._main_tab_widget.tabCloseRequested.connect(self._on_close_tab_requested)
        v_layout.addWidget(self._main_tab_widget)
        self._close_tab_shortcut = QShortcut(QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_W), self, self._on_close_tab_action)

        add_new_tab_button = QToolButton()
        add_new_tab_button.setFixedHeight(20)
        add_new_tab_button.setText("+")
        add_new_tab_button.setToolTip(self.tr("Create a new tab"))
        add_new_tab_button.clicked.connect(self._create_new_tab)
        self._main_tab_widget.setCornerWidget(add_new_tab_button, Qt.Corner.TopRightCorner)

        central_widget = QWidget()
        central_widget.setLayout(v_layout)
        self.setCentralWidget(central_widget)

        self._create_new_tab()

    def showEvent(self, _event: QShowEvent):
        if self._restore_geometry_on_show:
            self.load_state()

    def closeEvent(self, event):
        if not app_need_restart and not int(self._settings.get(Settings.DontAskAgainExit)):
            question = DontAskAgainQuestionDialog(app_name, self.tr("Exit?"))
            if question.exec() == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self._settings.set(Settings.DontAskAgainExit, question.is_dont_ask_again())

        event.accept()
        self.save_state()

    def load_state(self):
        geometry = self._settings.get(Settings.MainWindowGeometry)
        if not geometry.isEmpty():
            self.restoreGeometry(geometry)

        tabs_count = self._settings.begin_read_array(Settings.MainTabsArray)
        for tab_index in range(tabs_count):
            self._settings.set_array_index(tab_index)
            tab_widget = self._main_tab_widget.widget(0) if tab_index == 0 else self._create_new_tab()
            tab_widget.load_state()
        self._settings.end_array()
        current_tab_index = int(self._settings.get(Settings.ActiveTabIndex))
        self._main_tab_widget.setCurrentIndex(current_tab_index)
        self._restore_geometry_on_show = False

    def save_state(self):
        self._settings.set(Settings.MainWindowGeometry, self.saveGeometry())
        self._settings.begin_write_array(Settings.MainTabsArray)
        for tab_index in range(self._main_tab_widget.count()):
            self._settings.set_array_index(tab_index)
            tab_widget = self._main_tab_widget.widget(tab_index)
            tab_widget.save_state()
        self._settings.end_array()
        self._settings.set(Settings.ActiveTabIndex, self._main_tab_widget.currentIndex())

    def _create_new_tab(self):
        tab_widget = TabWidget(self._settings, self._main_tab_widget)
        tab_index = self._main_tab_widget.addTab(tab_widget, self.tr("New tab"))
        self._main_tab_widget.setCurrentIndex(tab_index)
        return tab_widget

    def _on_close_tab_requested(self, index):
        if self._main_tab_widget.count() > 1:
            self._main_tab_widget.removeTab(index)

    def _on_close_tab_action(self):
        if self._main_tab_widget.count() > 1:
            self._main_tab_widget.removeTab(self._main_tab_widget.currentIndex())

    def _get_file_path_to_export(self, caption: str, filter: str, file_suffix: str):
        current_workspace = self._main_tab_widget.currentWidget().current_workspace()
        data_name = current_workspace.get_data_name()
        if not data_name:
            data_name = "export"
        if not current_workspace or len(current_workspace.model.result) == 0:
            QMessageBox.warning(self, app_name, self.tr("There is no data to export"))
            return ""

        last_save_dir = self._settings.get(Settings.LastSaveDir)
        file_name = QFileDialog.getSaveFileName(self, caption=caption, filter=filter,
                                                dir=(last_save_dir + "/" + data_name + file_suffix))
        if not file_name[0]:
            return ""
        self._settings.set(Settings.LastSaveDir, QFileInfo(file_name[0]).dir().absolutePath())
        return file_name[0]

    def _on_export_xlsx(self):
        file_path = self._get_file_path_to_export(self.tr("Save XLSX"), self.tr("Xlsx File (*.xlsx)"), ".xlsx")
        if file_path:
            current_workspace = self._main_tab_widget.currentWidget().current_workspace()
            if current_workspace:
                export_to_xlsx(file_path, current_workspace.model)

    def _on_export_csv(self):
        file_path = self._get_file_path_to_export(self.tr("Save CSV"), self.tr("Csv File (*.csv)"), ".csv")
        if file_path:
            current_workspace = self._main_tab_widget.currentWidget().current_workspace()
            if current_workspace:
                export_to_csv(file_path, current_workspace.model)

    def _on_export_html(self):
        file_path = self._get_file_path_to_export(self.tr("Save HTML"), self.tr("Html File (*.html)"), ".html")
        if file_path:
            current_workspace = self._main_tab_widget.currentWidget().current_workspace()
            if current_workspace:
                export_to_html(file_path, current_workspace.model)

    def _on_preferences(self):
        global app_need_restart
        dialog = SettingsDialog(self._settings)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        Theme.apply(QApplication.instance(), int(self._settings.get(Settings.Theme)))

        for tab_index in range(self._main_tab_widget.count()):
            tab_widget = self._main_tab_widget.widget(tab_index)
            tab_widget.handle_preferences_change()

        if dialog.is_need_restart():
            app_need_restart = True
            self.close()

    def _on_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _on_authors(self):
        dialog = AuthorsDialog(self)
        dialog.exec()

    def _on_about_plugins(self):
        dialog = AboutPluginsDialog(plugin_manager, self)
        dialog.resize(640, 480)
        dialog.exec()


def top_exception_handler(_exctype, value, tb):
    dialog = QMessageBox(QMessageBox.Critical, app_name, str(value))
    if tb:
        format_exception = traceback.format_tb(tb)
        for line in format_exception:
            dialog.setDetailedText(str(line))
    dialog.exec()
    if window:
        window.save_state()
    app.exit(1)


sys.excepthook = top_exception_handler

app = QApplication(sys.argv)
window = None
app.setWindowIcon(QIcon("logo.png"))
app.setStyle("Fusion")
settings = Settings(app_name)
Theme.apply(app, int(settings.get(Settings.Theme)))

TabWidget.add_workspace_factory(SearchWorkspaceFactory())
TabWidget.add_workspace_factory(TrendsWorkspaceFactory())

plugin_manager = PluginManager()
plugin_manager.load_plugins()
for plugin in plugin_manager.get_plugins():
    plugin.initialize()

while True:
    app_translator: QTranslator = QTranslator()
    qt_translator: QTranslator = QTranslator()
    plugin_translators: list[QTranslator] = []
    if settings.get(Settings.Language) == "Ru":
        my_lang = "translations/ru.qm"
        qt_lang = "qtbase_ru.qm"
        if app_translator.load(my_lang):
            app.installTranslator(app_translator)
        if qt_translator.load(qt_lang, QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            app.installTranslator(qt_translator)
        for plugin in plugin_manager.get_plugins():
            plugin_lang = "translations/" + plugin.get_name() + "_ru.qm"
            plugin_translator = QTranslator()
            if plugin_translator.load(plugin_lang):
                app.installTranslator(plugin_translator)
                plugin_translators.append(plugin_translator)

    window = MainWindow(settings)
    window.resize(app.screens()[0].size() * 0.7)
    window.show()
    app.exec()

    if app_need_restart:
        app_need_restart = False
        app.removeTranslator(app_translator)
        app.removeTranslator(qt_translator)
        for plugin_translator in plugin_translators:
            app.removeTranslator(plugin_translator)
    else:
        break
