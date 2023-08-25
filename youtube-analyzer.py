import sys
import operator
import csv
from youtubesearchpython import (
    VideosSearch, 
    Channel
)
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel
)
from PySide6.QtGui import (
    QAction
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
    QSpacerItem
)
import xlsxwriter


app_name = "YouTube Analyzer"
version = "1.0"


def view_count_to_int(count_str):
    processed_count = count_str.split()[0].replace(",", "")
    return int(processed_count) if processed_count.isdigit() else 0


def subcriber_count_to_int(count_str):
    number_letter = count_str.split()[0]
    match number_letter[-1]:
        case "K":
            multiplier = 1000
        case "M":
            multiplier = 1000000
        case "B":
            multiplier = 1000000000
        case _:
            multiplier = 1
    return int(float(number_letter[:-1]) * multiplier)


class ResultTableModel(QAbstractTableModel):
    def __init__(self, parent, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.result = []
        self.header = header

    def setData(self, result):
        self.beginResetModel()
        self.result = result
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self.result.clear()
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.result)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.ItemDataRole.DisplayRole:
            return None
        return self.result[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        self.layoutAboutToBeChanged.emit()
        self.result = sorted(self.result, key=operator.itemgetter(col))
        if order == Qt.SortOrder.DescendingOrder:
            self.result.reverse()
        self.layoutChanged.emit()


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
        layout.addWidget(QLabel("Based on youtubesearchpython and PySide."), 
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
        header = ["Title", "Published Time", "Duration", 
                  "View Count", "Link", 
                  "Channel Name", "Channel Link", "Channel Subscribers",
                  "Channel Views", "Channel Joined Date",
                  "Views/Subscribers"]
        self._model = ResultTableModel(self, header)
        self._table_view = QTableView(self)
        self._table_view.setModel(self._model)
        self._table_view.resizeColumnsToContents()
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionsMovable(True)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._table_view)

        central_widget = QWidget()
        central_widget.setLayout(v_layout)
        self.setCentralWidget(central_widget)

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
        videos_search = VideosSearch(self._request_text, limit = request_limit)
        result = []
        has_next_page = True
        counter = 0
        while has_next_page:
            result_array = videos_search.result()["result"]
            for video in result_array:
                views = view_count_to_int(video["viewCount"]["text"])
                channel = Channel.get(video["channel"]["id"])
                channel_views = view_count_to_int(channel["views"])
                channel_subscribers = subcriber_count_to_int(channel["subscribers"]["simpleText"])
                result.append((video["title"], video["publishedTime"], video["duration"], 
                               views, video["link"],
                               channel["title"], channel["url"], channel_subscribers,
                               channel_views, channel["joinedDate"],
                               (str(round(views / channel_subscribers * 100, 2)) + "%")))
                counter = counter + 1
                if counter == request_limit:
                    break
            if counter == request_limit:
                break
            has_next_page = videos_search.next()
        self._model.setData(result)
        self._table_view.resizeColumnsToContents()
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
window = MainWindow()
window.resize(app.screens()[0].size() * 0.7)
window.show()
app.exec()
