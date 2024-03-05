import operator
from PySide2.QtCore import (
    Qt,
    QAbstractTableModel
)


def make_result_row(video_title: str, video_published_time: str, video_duration: str, 
                    views: int, video_link: str, channel_title: str, channel_link: str, 
                    channel_subscribers: int, channel_views: int, channel_joined_date: str,
                    video_preview_link: str, channel_logo_link: str, video_tags):
    view_rate = (str(round(views / channel_subscribers * 100, 2)) + "%") if channel_subscribers > 0 else "-"
    return (video_title, video_published_time, video_duration, views, video_link, channel_title, 
            channel_link, channel_subscribers, channel_views, channel_joined_date, view_rate, video_preview_link,
            channel_logo_link, video_tags)


class ResultFields:
    VideoTitle: int = 0
    VideoPublishedTime: int = 1
    VideoDuration: int = 2
    VideoViews: int = 3
    VideoLink: int = 4
    ChannelTitle: int = 5
    ChannelLink: int = 6
    ChannelSubscribers: int = 7
    ChannelViews: int = 8
    ChannelJoinedDate: int = 9
    ViewRate: int = 10
    VideoPreviewLink: int = 11
    ChannelLogoLink: int = 12
    VideoTags: int = 13


class ResultTableModel(QAbstractTableModel):
    SortRole: int = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.result = []
        self.header = [self.tr("Title"), self.tr("Published Time"), self.tr("Duration"), self.tr("View Count"), self.tr("Link"), 
                       self.tr("Channel Name"), self.tr("Channel Link"), self.tr("Channel Subscribers"),
                       self.tr("Channel Views"), self.tr("Channel Joined Date"), self.tr("Views/Subscribers")]
        self._sort_cast = {}

    def setData(self, result):
        self.beginResetModel()
        self.result = result
        self._sort_cast.clear()
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self.result.clear()
        self.endResetModel()

    def set_sort_cast(self, column: int, cast_func):
        self._sort_cast[column] = cast_func

    def rowCount(self, parent):
        return len(self.result)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role):
        if not index.isValid():
            return None
        column = index.column()
        if role == ResultTableModel.SortRole:
            if column in self._sort_cast:
                return self._sort_cast[column](self.result[index.row()][column])
            if column == ResultFields.ViewRate:
                return float(self.result[index.row()][column][:-1])
            return self.result[index.row()][column]
        elif role == Qt.ItemDataRole.DisplayRole:
            if column == ResultFields.VideoTitle or column == ResultFields.ChannelTitle:
                return None
            return self.result[index.row()][column]

        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.header[col]
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        reverse = order == Qt.SortOrder.DescendingOrder
        self.result = sorted(self.result, key=operator.itemgetter(column), reverse=reverse)
        self.layoutChanged.emit()


class DataCache:
    def __init__(self):
        self._images = {}

    def cache_image(self, url, image):
        self._images[url] = image

    def get_image(self, url):
        return self._images[url] if url in self._images else None

    def clear(self):
        self._images.clear()
