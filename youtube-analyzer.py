import sys
import operator
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
    QFileDialog
)
import xlsxwriter


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._request_text = ""

        self.setWindowTitle("YouTube Analyzer")

        file_menu = self.menuBar().addMenu("File")
        export_xlsx_action = file_menu.addAction( "Export to XLSX..." )
        export_xlsx_action.triggered.connect(self._on_export_xlsx)

        h_layout = QHBoxLayout()
        self._search_line_edit = QLineEdit()
        self._search_line_edit.returnPressed.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_line_edit)
        self._search_button = QPushButton("Search")
        self._search_button.clicked.connect(self._on_search_clicked)
        h_layout.addWidget(self._search_button)

        v_layout = QVBoxLayout()
        header = ["Title", "Published Time", "Duration", 
                  "View Count", "Link", 
                  "Channel Name", "Channel Link", "Channel Subscribers",
                  "Channel Views", "Channel Joined Date"]
        self._model = ResultTableModel(self, header)
        self._table_view = QTableView(self)
        self._table_view.setModel(self._model)
        self._table_view.resizeColumnsToContents()
        self._table_view.setSortingEnabled(True)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._table_view)

        central_widget = QWidget()
        central_widget.setLayout(v_layout)
        self.setCentralWidget(central_widget)

    def _on_search_clicked(self):
        self._request_text = self._search_line_edit.text()
        request_limit = 30

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
                               channel_views, channel["joinedDate"]))
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


app = QApplication(sys.argv)
window = MainWindow()
window.resize(app.screens()[0].size() * 0.7)
window.show()
app.exec()
