import sys
import csv
from PySide6.QtCore import (
    Qt,
    QFileInfo,
    QSortFilterProxyModel,
    QTranslator,
    QLibraryInfo
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
    QCheckBox
)
import xlsxwriter
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


app_name = "YouTube Analyzer"
version = "2.0dev"

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
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(53, 53, 53).lighter());
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(53, 53, 53).lighter());
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(53, 53, 53).lighter());
            palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53));
            app.setPalette(palette)
        else:
            app.setPalette(QPalette())


class DontAskAgainQuestionDialog(QMessageBox):
    def __init__(self, title: str, text: str, parent = None):
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
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About"))
        layout = QGridLayout()
        layout.setSizeConstraint( QGridLayout.SizeConstraint.SetFixedSize )
        
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
        layout.addWidget(QLabel(self.tr("Based on youtubesearchpython and PySide6")), 
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
        layout.addWidget(QLabel("Copyright 2023 Alexander Trotsenko"), row, 0, 1, 2,
                         Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel(self.tr("All rights reserved")), row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

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
        file_menu.addSeparator()
        exit_action = file_menu.addAction(self.tr("Exit"))
        exit_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Q))
        exit_action.triggered.connect(self.close)

        edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        preferences_action = edit_menu.addAction(self.tr("Preferences..."))
        preferences_action.triggered.connect(self._on_preferences)

        help_menu = self.menuBar().addMenu(self.tr("Help"))
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

        v_layout = QVBoxLayout()
        self._model = ResultTableModel(self)
        self._sort_model = QSortFilterProxyModel(self)
        self._sort_model.setSortRole(ResultTableModel.SortRole)
        self._sort_model.setSourceModel(self._model)
        self._table_view = QTableView(self)
        self._table_view.setModel(self._sort_model)
        self._table_view.resizeColumnsToContents()
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionsMovable(True)
        self._table_view.setColumnHidden(ResultFields.VideoLink, True) # Hide column because the link is on video title
        self._table_view.setColumnHidden(ResultFields.ChannelLink, True) # Hide column because the link is on channel title
        self._table_view.setColumnHidden(ResultFields.ChannelViews, True) # It's not supported in yotubesearchpython
        self._table_view.setColumnHidden(ResultFields.ChannelJoinedDate, True) # It's not supported in yotubesearchpython
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._table_view)

        central_widget = QWidget()
        central_widget.setLayout(v_layout)
        self.setCentralWidget(central_widget)

    def showEvent(self, event: QShowEvent):
        if self._restore_geometry_on_show:
            self.restoreGeometry(self._settings.get(Settings.MainWindowGeometry))
            self._restore_geometry_on_show = False

    def closeEvent(self, event):
        global app_need_restart
        if not app_need_restart and not int(self._settings.get(Settings.DontAskAgainExit)):
            question = DontAskAgainQuestionDialog(app_name, self.tr("Exit?"))
            if question.exec() == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self._settings.set(Settings.DontAskAgainExit, question.is_dont_ask_again())

        event.accept()
        self._settings.set(Settings.MainWindowGeometry, self.saveGeometry())

    def _on_search_clicked(self):
        self._request_text = self._search_line_edit.text()
        request_limit = self._search_limit_spin_box.value()

        if self._request_text == "":
            return

        self._settings.set(Settings.RequestLimit, request_limit)

        self._search_line_edit.setDisabled(True)
        self._search_button.setDisabled(True)
        self._table_view.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self._model.clear()
        self._sort_model.sort(-1)
        QApplication.instance().processEvents()

        engine = self._create_engine()
        if engine.search(self._request_text):
            for i in range(len(self._model.result)):
                video_idx = self._sort_model.index(i, ResultFields.VideoTitle)
                video_item = self._model.result[i]
                video_label = self._create_link_label(video_item[ResultFields.VideoLink], video_item[ResultFields.VideoTitle])
                self._table_view.setIndexWidget(video_idx, video_label);
                
                channel_idx = self._sort_model.index(i, ResultFields.ChannelTitle)
                channel_label = self._create_link_label(video_item[ResultFields.ChannelLink], video_item[ResultFields.ChannelTitle])
                self._table_view.setIndexWidget(channel_idx, channel_label);
            
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

    def _on_export_xlsx(self):
        if self._request_text == "" or len(self._model.result) == 0:
            return

        last_save_dir = self._settings.get(Settings.LastSaveDir)
        file_name = QFileDialog.getSaveFileName(self, caption=self.tr("Save XLSX"), filter='Xlsx File (*.xlsx)',
                                                dir=(last_save_dir + "/" + self._request_text + ".xlsx"))
        if not file_name[0]:
            return
        self._settings.set(Settings.LastSaveDir, QFileInfo(file_name[0]).dir().absolutePath())
        
        workbook = xlsxwriter.Workbook(file_name[0])
        worksheet = workbook.add_worksheet()

        for column in range(len(self._model.header)):
            worksheet.write(0, column, self._model.header[column])

        for row in range(len(self._model.result)):
            for column in range(len(self._model.header)):
                worksheet.write(row + 1, column, self._model.result[row][column])

        worksheet.autofit()
        workbook.close()

    def _on_export_csv(self):
        if self._request_text == "" or len(self._model.result) == 0:
            return

        last_save_dir = self._settings.get(Settings.LastSaveDir)
        file_name = QFileDialog.getSaveFileName(self, caption=self.tr("Save CSV"), filter="Csv File (*.csv)",
                                                dir=(last_save_dir + "/" + self._request_text + ".csv"))
        if not file_name[0]:
            return
        self._settings.set(Settings.LastSaveDir, QFileInfo(file_name[0]).dir().absolutePath())

        with open(file_name[0], 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=';')
            csv_writer.writerow(self._model.header)
            for result_item in self._model.result:
                csv_writer.writerow(result_item)

    def _on_preferences(self):
        global app_need_restart
        dialog = SettingsDialog(self._settings)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            Theme.apply(QApplication.instance(), int(self._settings.get(Settings.Theme)))
            if dialog.is_need_restart():
                app_need_restart = True
                self.close()

    def _on_about(self):
        dialog = AboutDialog(self)
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


app = QApplication(sys.argv)
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
