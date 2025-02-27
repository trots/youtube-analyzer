import operator
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel
)


def make_result_row(video_title: str, video_published_time: str, video_duration: str,
                    views: int, video_link: str, channel_title: str, channel_link: str,
                    channel_subscribers: int, channel_views: int, channel_joined_date: str,
                    video_preview_link: str, channel_logo_link: str, video_tags: list[str],
                    video_duration_timedelta, video_relevance_number, video_type):
    view_rate = (str(round(views / channel_subscribers * 100, 2)) + "%") if channel_subscribers > 0 else "-"
    return (video_title, video_published_time, video_duration, views, video_link, channel_title,
            channel_link, channel_subscribers, channel_views, channel_joined_date, view_rate, video_preview_link,
            channel_logo_link, video_tags, video_duration_timedelta, video_relevance_number, video_type)


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
    VideoDurationTimedelta: int = 14
    VideoRelevanceNumber: int = 15
    VideoType: int = 16
    MaxFieldsCount: int = 17  # Add new items before this line


class ResultTableModel(QAbstractTableModel):
    SortRole: int = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.result = []
        self.FieldNames = [
            self.tr("Title"),
            self.tr("Published Time"),
            self.tr("Duration"),
            self.tr("View Count"),
            self.tr("Link"),
            self.tr("Channel Name"),
            self.tr("Channel Link"),
            self.tr("Channel Subscribers"),
            self.tr("Channel Views"),
            self.tr("Channel Joined Date"),
            self.tr("Views/Subscribers"),
            self.tr("Preview Link"),
            self.tr("Channel Logo Link"),
            self.tr("Video Tags"),
            self.tr("Video Duration Timedelta"),
            self.tr("#"),
            self.tr("Type")
            ]
        self.FieldTooltips = [
            self.tr("Video title"),
            self.tr("Video published time"),
            self.tr("Video duration"),
            self.tr("Video view count"),
            self.tr("Video link"),
            self.tr("Channel name"),
            self.tr("Channel link"),
            self.tr("Channel subscriber count"),
            self.tr("Channel view count"),
            self.tr("Channel registration date"),
            self.tr("Video views to channel subscribers ratio in percents"),
            self.tr("Preview image link"),
            self.tr("Channel logo image link"),
            self.tr("Video tag list"),
            self.tr("Video duration timedelta"),
            self.tr("Video relevance in search output (0 is the higest relevance)"),
            self.tr("Video type")
            ]
        self._fields = [
            ResultFields.VideoRelevanceNumber,
            ResultFields.VideoTitle,
            ResultFields.VideoType,
            ResultFields.VideoPublishedTime,
            ResultFields.VideoDuration,
            ResultFields.VideoViews,
            ResultFields.ChannelTitle,
            ResultFields.ChannelSubscribers,
            ResultFields.ViewRate
        ]
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

    def has_data(self):
        return len(self.result) > 0

    def set_sort_cast(self, column: int, cast_func):
        self._sort_cast[column] = cast_func

    def get_field_column(self, result_field: ResultFields):
        for i in range(len(self._fields)):
            if self._fields[i] == result_field:
                return i
        return -1

    def get_field_data(self, row: int, result_field: ResultFields):
        if row is None or row < 0 or row >= len(self.result):
            return None
        return self.result[row][result_field]

    def rowCount(self, parent):
        return len(self.result)

    def columnCount(self, parent):
        return len(self._fields)

    def data(self, index, role):
        if not index.isValid():
            return None
        row = index.row()
        column = self._fields[index.column()]
        if role == ResultTableModel.SortRole:
            if column in self._sort_cast:
                return self._sort_cast[column](self.result[row][column])
            if column == ResultFields.ViewRate:
                return float(self.result[row][column][:-1])
            return self.result[row][column]
        elif role == Qt.ItemDataRole.DisplayRole:
            if column == ResultFields.VideoTitle or column == ResultFields.ChannelTitle:
                return None
            if column == ResultFields.VideoViews or column == ResultFields.ChannelSubscribers:
                update_data = '{0:,}'.format(self.result[row][column]).replace(',', ' ')
                return update_data
            return self.result[row][column]

        return None

    def headerData(self, column, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.FieldNames[self._fields[column]]
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.FieldTooltips[self._fields[column]]
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


class VideoCategory:
    def __init__(self, id: int, text: str):
        self.id = id
        self.text = text
