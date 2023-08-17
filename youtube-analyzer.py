import sys
import csv
from youtubesearchpython import (
    VideosSearch, 
    Channel
)
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QFileDialog
)


def view_count_to_int(count_str):
    return int(count_str.split()[0].replace(',', ''))


def subcriber_count_to_int(count_str):
    number_letter = count_str.split()[0]
    match number_letter[-1]:
        case 'K':
            multiplier = 1000
        case 'M':
            multiplier = 1000000
        case 'B':
            multiplier = 1000000000
        case _:
            multiplier = 1
    return int(float(number_letter[:-1]) * multiplier)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('YouTube Analyzer')

        layout = QHBoxLayout()
        self._search_line_edit = QLineEdit()
        self._search_line_edit.returnPressed.connect(self._on_search_clicked)
        layout.addWidget(self._search_line_edit)
        self._search_button = QPushButton("Search...")
        self._search_button.clicked.connect(self._on_search_clicked)
        layout.addWidget(self._search_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _on_search_clicked(self):
        request_text = self._search_line_edit.text()
        request_limit = 30

        if request_text == "":
            return

        videos_search = VideosSearch(request_text, limit = request_limit)

        file_name = QFileDialog.getSaveFileName(self, caption='Open Image', filter='Csv File (*.csv)',
                                                dir=(request_text + ".csv"))

        with open(file_name[0], 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=';')
            csv_writer.writerow(['Title', 'Published Time', 'Duration', 
                                'View Count', 'Link', 
                                'Channel Name', 'Channel Link', 'Channel Subscribers',
                                'Channel Views', 'Channel Joined Date'])
            has_next_page = True
            counter = 0
            while has_next_page:
                result_array = videos_search.result()["result"]
                for video in result_array:
                    views = view_count_to_int(video['viewCount']['text'])
                    channel = Channel.get(video['channel']['id'])
                    channel_views = view_count_to_int(channel['views'])
                    channel_subscribers = subcriber_count_to_int(channel['subscribers']['simpleText'])
                    csv_writer.writerow([video['title'], video['publishedTime'], video['duration'], 
                                        views, video['link'],
                                        channel['title'], channel['url'], channel_subscribers,
                                        channel_views, channel['joinedDate']])
                    counter = counter + 1
                    if counter == request_limit:
                        break
                if counter == request_limit:
                    break
                has_next_page = videos_search.next()

app = QApplication(sys.argv)
window = MainWindow()
window.resize(400, 50)
window.show()
app.exec()
