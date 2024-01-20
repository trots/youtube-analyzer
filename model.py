import operator
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel
)


def make_result_row(video_title: str, video_published_time: str, video_duration: str, 
                    views: int, video_link: str, channel_title: str, channel_url: str, 
                    channel_subscribers: int, channel_views: int, channel_joined_date: str):
    view_rate = (str(round(views / channel_subscribers * 100, 2)) + "%") if channel_subscribers > 0 else "-"
    return (video_title, video_published_time, video_duration, views, video_link, channel_title, 
            channel_url, channel_subscribers, channel_views, channel_joined_date, view_rate)


class ResultTableModel(QAbstractTableModel):
    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.result = []
        self.header = ["Title", "Published Time", "Duration", "View Count", "Link", 
                       "Channel Name", "Channel Link", "Channel Subscribers",
                       "Channel Views", "Channel Joined Date", "Views/Subscribers"]

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
