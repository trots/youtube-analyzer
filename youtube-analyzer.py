import sys
import csv
from PySide6.QtCore import (
    Qt
)
from PySide6.QtGui import (
    QAction,
    QIcon
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
    QMessageBox
)
import xlsxwriter
from model import (
    ResultTableModel
)
from engine import (
    YoutubeGrepEngine
)


app_name = "YouTube Analyzer"
version = "2.0dev"


class AboutDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("About")
        layout = QGridLayout()
        layout.setSizeConstraint( QGridLayout.SizeConstraint.SetFixedSize )
        
        row = 0
        title = QLabel(app_name)
        title.setStyleSheet("font-size: 14px")
        layout.addWidget(title, row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel("Software for analyzing of YouTube search output."), row, 0, 1, 2,
                         Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel("Version: " + version), 
                         row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel("Based on youtubesearchpython and PySide6."), 
                         row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        row += 1
        vertical_spacer = QSpacerItem(1, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vertical_spacer, row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        row += 1
        layout.addWidget(QLabel("Web site:"), row, 0, Qt.AlignmentFlag.AlignRight)
        site = QLabel("<a href=\"https://github.com/trots/youtube-analyzer\">https://github.com/trots/youtube-analyzer</a>")
        site.setOpenExternalLinks(True)
        layout.addWidget(site, row, 1)
        row += 1
        layout.addWidget(QLabel("License:"), row, 0, Qt.AlignmentFlag.AlignRight)
        lic = QLabel("<a href=\"https://github.com/trots/youtube-analyzer/blob/master/LICENSE\">MIT License</a>")
        lic.setOpenExternalLinks(True)
        layout.addWidget(lic, row, 1)

        row += 1
        vertical_spacer = QSpacerItem(1, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vertical_spacer, row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        row += 1
        layout.addWidget(QLabel("Copyright 2023 Alexander Trotsenko."), row, 0, 1, 2,
                         Qt.AlignmentFlag.AlignCenter)
        row += 1
        layout.addWidget(QLabel("All rights reserved."), row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._request_text = ""

        self.setWindowTitle(app_name + " " + version)

        file_menu = self.menuBar().addMenu("File")
        export_xlsx_action = file_menu.addAction("Export to XLSX...")
        export_xlsx_action.triggered.connect(self._on_export_xlsx)
        export_csv_action = file_menu.addAction("Export to CSV...")
        export_csv_action.triggered.connect(self._on_export_csv)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        help_menu = self.menuBar().addMenu("Help")
        about_action = help_menu.addAction("About...")
        about_action.triggered.connect(self._on_about)

        h_layout = QHBoxLayout()
        self._search_line_edit = QLineEdit()
        self._search_line_edit.setPlaceholderText("Enter request and press 'Search'...")
        self._search_line_edit.setToolTip(self._search_line_edit.placeholderText())
        self._search_line_edit.returnPressed.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_line_edit)
        self._search_limit_spin_box = QSpinBox()
        self._search_limit_spin_box.setToolTip("Set the search result limit")
        self._search_limit_spin_box.setMinimumWidth(50)
        self._search_limit_spin_box.setRange(2, 30)
        self._search_limit_spin_box.setValue(10)
        h_layout.addWidget(self._search_limit_spin_box)
        self._search_button = QPushButton("Search")
        self._search_button.setToolTip("Click to start searching")
        self._search_button.clicked.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_button)

        v_layout = QVBoxLayout()
        self._model = ResultTableModel(self)
        self._table_view = QTableView(self)
        self._table_view.setModel(self._model)
        self._table_view.resizeColumnsToContents()
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionsMovable(True)
        self._table_view.setColumnHidden(8, True) # Hide channel views column because it's not supported in yotubesearchpython
        self._table_view.setColumnHidden(9, True) # Hide channel join date column because it's not supported in yotubesearchpython
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._table_view)

        central_widget = QWidget()
        central_widget.setLayout(v_layout)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        if QMessageBox.question(self, app_name, "Exit?") == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def _on_search_clicked(self):
        self._request_text = self._search_line_edit.text()
        request_limit = self._search_limit_spin_box.value()

        if self._request_text == "":
            return

        self._search_line_edit.setDisabled(True)
        self._search_button.setDisabled(True)
        self._table_view.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self._model.clear()
        QApplication.instance().processEvents()

        engine = YoutubeGrepEngine(self._model, request_limit)
        if engine.search(self._request_text):
            self._table_view.resizeColumnsToContents()
        else:
            dialog = QMessageBox()
            dialog.setWindowTitle(app_name)
            dialog.setText("Error in the searching process")
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

        file_name = QFileDialog.getSaveFileName(self, caption="Save XLSX", filter='Xlsx File (*.xlsx)',
                                                dir=(self._request_text + ".xlsx"))
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

        file_name = QFileDialog.getSaveFileName(self, caption="Save CSV", filter="Csv File (*.csv)",
                                                dir=(self._request_text + ".csv"))

        with open(file_name[0], 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=';')
            csv_writer.writerow(self._model.header)
            for result_item in self._model.result:
                csv_writer.writerow(result_item)

    def _on_about(self):
        dialog = AboutDialog(self)
        dialog.exec()


app = QApplication(sys.argv)
app.setWindowIcon(QIcon("logo.png"))
window = MainWindow()
window.resize(app.screens()[0].size() * 0.7)
window.show()
app.exec()
