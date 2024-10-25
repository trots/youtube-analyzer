import sys
import traceback

from PySide6.QtCore import (
    Qt,
    QFileInfo,
    QSortFilterProxyModel,
    QTranslator,
    QLibraryInfo,
    QItemSelection,
    QTimer
)
from PySide6.QtGui import (
    QKeySequence,
    QIcon,
    QShowEvent,
    QPalette,
    QColor
)
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QTableView,
    QFileDialog,
    QSpinBox,
    QDialog,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QMessageBox,
    QCheckBox,
    QSplitter,
    QTextEdit,
    QTabWidget
)
from PySide6.QtCharts import (
    QChart
)
from defines import (
    app_name,
    version
)
from settings import (
    Settings,
    SettingsDialog
)
from model import (
    ResultFields,
    ResultTableModel
)
from engine import (
    YoutubeGrepEngine,
    YoutubeApiEngine
)
from widgets import (
    VideoDetailsWidget,
    AnalyticsWidget
)
from export import (
    export_to_xlsx,
    export_to_csv,
    export_to_html
)


app_need_restart = False


class Theme:
    System: int = 0
    Dark: int = 1

    @staticmethod
    def apply(app: QApplication, theme_index: int):
        if theme_index == Theme.Dark:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.black)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(148, 192, 236))
            palette.setColor(QPalette.Highlight, QColor(19, 60, 110))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(53, 53, 53).lighter())
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(53, 53, 53).lighter())
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(53, 53, 53).lighter())
            palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53))
            app.setPalette(palette)
        else:
            palette = QPalette()
            palette.setColor(QPalette.Link, QColor(19, 60, 110))
            app.setPalette(palette)


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


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self._request_text = ""
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
        exit_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Q))
        exit_action.triggered.connect(self.close)

        edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        preferences_action = edit_menu.addAction(self.tr("Preferences..."))
        preferences_action.triggered.connect(self._on_preferences)

        view_menu = self.menuBar().addMenu(self.tr("View"))
        self._show_details_action = view_menu.addAction(self.tr("Show details"))
        self._show_details_action.setCheckable(True)
        self._show_details_action.setChecked(False)

        help_menu = self.menuBar().addMenu(self.tr("Help"))
        authors_action = help_menu.addAction(self.tr("Authors..."))
        authors_action.triggered.connect(self._on_authors)
        about_action = help_menu.addAction(self.tr("About..."))
        about_action.triggered.connect(self._on_about)

        h_layout = QHBoxLayout()
        self._search_line_edit = QLineEdit()
        self._search_line_edit.setPlaceholderText(self.tr("Enter request and press 'Search'..."))
        self._search_line_edit.setToolTip(self._search_line_edit.placeholderText())
        self._search_line_edit.returnPressed.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_line_edit)
        self._search_limit_spin_box = QSpinBox()
        self._search_limit_spin_box.setToolTip(self.tr("Set the search result limit"))
        self._search_limit_spin_box.setMinimumWidth(50)
        self._search_limit_spin_box.setRange(2, 30)
        request_limit = int(self._settings.get(Settings.RequestLimit))
        self._search_limit_spin_box.setValue(request_limit)
        h_layout.addWidget(self._search_limit_spin_box)
        self._search_button = QPushButton(self.tr("Search"))
        self._search_button.setToolTip(self.tr("Click to start searching"))
        self._search_button.clicked.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_button)

        self._model = ResultTableModel(self)
        self._sort_model = QSortFilterProxyModel(self)
        self._sort_model.setSortRole(ResultTableModel.SortRole)
        self._sort_model.setSourceModel(self._model)
        self._table_view = QTableView(self)
        self._table_view.setModel(self._sort_model)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionsMovable(True)
        self._table_view.selectionModel().selectionChanged.connect(self._on_table_row_changed)

        self._side_tab_widget = QTabWidget()
        self._side_tab_widget.setVisible(False)
        self._show_details_action.toggled.connect(self._on_switch_side_panel)

        self._details_widget = VideoDetailsWidget(self._model, self)
        self._details_widget.setVisible(False)

        self._analytics_widget = AnalyticsWidget(self._model, self)
        self._analytics_widget.setVisible(False)
        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)
        self._analytics_widget.set_current_chart_index(int(self._settings.get(Settings.LastActiveChartIndex)))

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setChildrenCollapsible(False)
        self._main_splitter.addWidget(self._table_view)
        self._main_splitter.addWidget(self._side_tab_widget)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._main_splitter)

        central_widget = QWidget()
        central_widget.setLayout(v_layout)
        self.setCentralWidget(central_widget)

    def showEvent(self, _event: QShowEvent):
        if self._restore_geometry_on_show:
            # Restore window geometry
            geometry = self._settings.get(Settings.MainWindowGeometry)
            if not geometry.isEmpty():
                self.restoreGeometry(geometry)
            # Restore main splitter sizes
            splitter_sizes = list(map(int, self._settings.get(Settings.MainSplitterState)))
            if len(splitter_sizes) != 2 or splitter_sizes[0] == 0 or splitter_sizes[1] == 0:
                window_width_part = self.width() / 5
                splitter_sizes = [3 * window_width_part, 2 * window_width_part]
            self._main_splitter.setSizes(splitter_sizes)
            # Restore details panel visibility
            if self._settings.get(Settings.DetailsVisible):
                self._show_details_action.setChecked(True)
            self._restore_geometry_on_show = False
            # Restore main table
            table_header_state = self._settings.get(Settings.MainTableHeaderState)
            if not table_header_state.isEmpty():
                self._table_view.horizontalHeader().restoreState(table_header_state)
        self._table_view.resizeColumnsToContents()

    def closeEvent(self, event):
        global app_need_restart
        if not app_need_restart and not int(self._settings.get(Settings.DontAskAgainExit)):
            question = DontAskAgainQuestionDialog(app_name, self.tr("Exit?"))
            if question.exec() == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self._settings.set(Settings.DontAskAgainExit, question.is_dont_ask_again())

        event.accept()
        self.save_state()

    def save_state(self):
        self._settings.set(Settings.MainWindowGeometry, self.saveGeometry())
        self._settings.set(Settings.DetailsVisible, self._show_details_action.isChecked())
        self._settings.set(Settings.LastActiveChartIndex, self._analytics_widget.get_current_chart_index())
        self._settings.set(Settings.MainTableHeaderState, self._table_view.horizontalHeader().saveState())
        if self._show_details_action.isChecked():
            self._settings.set(Settings.MainSplitterState, self._main_splitter.sizes())
            self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.currentIndex())

    def _on_switch_side_panel(self, visible):
        # Workaround for the hide/show bug of the QTabWidget.
        # Bug: If QTabWidget has the current tab index > 0, then QTabWidget hides first tab forever after hide/show iteration.
        # So we need remove/add all tabs after hide/show to fix this bug.
        if visible:
            self._side_tab_widget.addTab(self._details_widget, self.tr("Details"))
            self._side_tab_widget.addTab(self._analytics_widget, self.tr("Analytics"))
            self._side_tab_widget.show()
            QTimer.singleShot(0, lambda: self._side_tab_widget.setCurrentIndex(
                              int(self._settings.get(Settings.LastActiveDetailsTab))))
        else:
            self._settings.set(Settings.MainSplitterState, self._main_splitter.sizes())
            self._settings.set(Settings.LastActiveDetailsTab, self._side_tab_widget.currentIndex())
            self._side_tab_widget.hide()
            self._side_tab_widget.removeTab(1)
            self._side_tab_widget.removeTab(0)

    def _on_search_clicked(self):
        self._request_text = self._search_line_edit.text()
        request_limit = self._search_limit_spin_box.value()

        if self._request_text == "":
            return

        self._settings.set(Settings.RequestLimit, request_limit)

        self._search_line_edit.setDisabled(True)
        self._search_button.setDisabled(True)
        self._table_view.setDisabled(True)
        self._side_tab_widget.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self._model.clear()
        self._sort_model.sort(-1)
        self._details_widget.clear()
        QApplication.instance().processEvents()

        engine = self._create_engine()
        if engine.search(self._request_text):
            for i in range(len(self._model.result)):
                video_idx = self._sort_model.index(i, self._model.get_field_column(ResultFields.VideoTitle))
                video_item = self._model.result[i]
                video_label = self._create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label)

                channel_idx = self._sort_model.index(i, self._model.get_field_column(ResultFields.ChannelTitle))
                channel_label = self._create_link_label(video_item[ResultFields.ChannelLink],
                                                        video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label)

            self._table_view.resizeColumnsToContents()
        else:
            dialog = QMessageBox()
            dialog.setWindowTitle(app_name)
            dialog.setText(self.tr("Error in the searching process"))
            dialog.setIcon(QMessageBox.Critical)
            dialog.setDetailedText(engine.error)
            dialog.exec()

        QApplication.restoreOverrideCursor()
        self._search_line_edit.setDisabled(False)
        self._search_button.setDisabled(False)
        self._table_view.setDisabled(False)
        self._side_tab_widget.setDisabled(False)

    def _on_table_row_changed(self, current: QItemSelection, _previous: QItemSelection):
        indexes = current.indexes()
        if len(indexes) > 0:
            index = self._sort_model.mapToSource(indexes[0])
            self._details_widget.set_current_index(index)
            self._analytics_widget.set_current_index(index)
        else:
            self._details_widget.set_current_index(None)
            self._analytics_widget.set_current_index(None)

    def _get_file_path_to_export(self, caption: str, filter: str, file_suffix: str):
        if self._request_text == "" or len(self._model.result) == 0:
            return ""

        last_save_dir = self._settings.get(Settings.LastSaveDir)
        file_name = QFileDialog.getSaveFileName(self, caption=caption, filter=filter,
                                                dir=(last_save_dir + "/" + self._request_text + file_suffix))
        if not file_name[0]:
            return ""
        self._settings.set(Settings.LastSaveDir, QFileInfo(file_name[0]).dir().absolutePath())
        return file_name[0]

    def _on_export_xlsx(self):
        file_path = self._get_file_path_to_export(self.tr("Save XLSX"), self.tr("Xlsx File (*.xlsx)"), ".xlsx")
        if file_path:
            export_to_xlsx(file_path, self._model)

    def _on_export_csv(self):
        file_path = self._get_file_path_to_export(self.tr("Save CSV"), self.tr("Csv File (*.csv)"), ".csv")
        if file_path:
            export_to_csv(file_path, self._model)

    def _on_export_html(self):
        file_path = self._get_file_path_to_export(self.tr("Save HTML"), self.tr("Html File (*.html)"), ".html")
        if file_path:
            export_to_html(file_path, self._model)

    def _on_preferences(self):
        global app_need_restart
        dialog = SettingsDialog(self._settings)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        Theme.apply(QApplication.instance(), int(self._settings.get(Settings.Theme)))
        if int(self._settings.get(Settings.Theme)) == Theme.Dark:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeDark)
        else:
            self._analytics_widget.set_charts_theme(QChart.ChartTheme.ChartThemeLight)

        self._analytics_widget.set_current_index_following(self._settings.get(Settings.AnalyticsFollowTableSelect))
        if self._settings.get(Settings.AnalyticsFollowTableSelect):
            self._analytics_widget.set_current_index(self._table_view.currentIndex())

        if dialog.is_need_restart():
            app_need_restart = True
            self.close()

    def _on_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _on_authors(self):
        dialog = AuthorsDialog(self)
        dialog.exec()

    def _create_engine(self):
        request_limit = self._search_limit_spin_box.value()
        api_key = self._settings.get(Settings.YouTubeApiKey)
        if not api_key:
            return YoutubeGrepEngine(self._model, request_limit)
        else:
            return YoutubeApiEngine(self._model, request_limit, api_key)

    def _create_link_label(self, link: str, text: str):
        label = QLabel("<a href=\"" + link + "\">" + text + "</a>")
        label_size_policy = label.sizePolicy()
        label_size_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        label.setSizePolicy(label_size_policy)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)
        return label


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

while True:
    my_translator = QTranslator()
    qt_translator = QTranslator()
    if settings.get(Settings.Language) == "Ru":
        my_lang = "translations/ru.qm"
        qt_lang = "qtbase_ru.qm"
    else:
        my_lang = "translations/en.qm"
        qt_lang = "qtbase_en.qm"
    if my_translator.load(my_lang):
        app.installTranslator(my_translator)
    if qt_translator.load(qt_lang, QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(qt_translator)

    window = MainWindow(settings)
    window.resize(app.screens()[0].size() * 0.7)
    window.show()
    app.exec()

    if app_need_restart:
        app_need_restart = False
    else:
        break
