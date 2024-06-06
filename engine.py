from datetime import datetime, timedelta
import traceback
import isodate
from PySide6.QtCore import (
    QObject,
    Signal,
    QUrl
)
from PySide6.QtGui import (
    QImage
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply
)
from youtubesearchpython import (
    VideosSearch, 
    Channel,
    Video
)
import googleapiclient.discovery
from model import (
    make_result_row,
    ResultFields,
    ResultTableModel,
    DataCache
)


def view_count_to_int(count_str: str):
    if not count_str:
        return 0
    parts = count_str.split()
    if len(parts) == 0:
        return 0
    processed_count = parts[0].replace(",", "")
    return int(processed_count) if processed_count.isdigit() else 0


def subcriber_count_to_int(count_str: str):
    if not count_str:
        return 0
    parts = count_str.split()
    if len(parts) == 0:
        return 0
    number_letter = parts[0]
    match number_letter[-1]:
        case "K":
            multiplier = 1000
        case "M":
            multiplier = 1000000
        case "B":
            multiplier = 1000000000
        case _:
            multiplier = 1
    if multiplier == 1:
        return int(number_letter)
    return int(float(number_letter[:-1]) * multiplier)


def timedelta_to_str(td: timedelta):
        if td is None:
            return ""
        mm, ss = divmod(td.seconds, 60)
        hh, mm = divmod(mm, 60)
        s = "%02d:%02d:%02d" % (hh, mm, ss)
        if td.days:
            s = ("%d:" % td.days) + s
        if td.microseconds:
            s = s + ".%06d" % td.microseconds
        return s


class ImageDownloader(QObject):
    finished = Signal(QImage)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._try_again = True
        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._handle_finished)
        self._data_cache = DataCache()

    def start_download(self, url: QUrl):
        image = self._data_cache.get_image(url.toString())
        if image is not None:
            self.finished.emit(image)
        else:
            self._manager.clearConnectionCache()
            self._manager.get(QNetworkRequest(url))

    def clear_cache(self):
        self._manager.clearAccessCache()
        self._data_cache.clear()

    def _handle_finished(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            self.error.emit(reply.errorString())
            return
        image = QImage()
        image.loadFromData(reply.readAll())
        if image.isNull() and self._try_again:
            self._manager.get(QNetworkRequest(reply.url()))
            self._try_again = False
        self._try_again = True
        self._data_cache.cache_image(reply.url().toString(), image)
        self.finished.emit(image)


class AbstractYoutubeEngine:
    def __init__(self, model: ResultTableModel, request_limit: int):
        self.error = ""
        self._model = model
        self._request_limit = request_limit

    def search(self, request_text: str):
        pass


class YoutubeGrepEngine(AbstractYoutubeEngine):
    def __init__(self, model: ResultTableModel, request_limit: int):
        super().__init__(model, request_limit)

    def search(self, request_text: str):
        try:
            self.error = ""
            videos_search = self._create_video_searcher(request_text)
            result = []
            has_next_page = True
            counter = 0
            while has_next_page:
                result_array = videos_search.result()["result"]
                for video in result_array:
                    views = view_count_to_int(video["viewCount"]["text"])
                    video_info = self._get_video_info(video["id"])
                    channel_info = self._get_channel_info(video["channel"]["id"])
                    channel_views = view_count_to_int(channel_info["views"])
                    channel_subscribers = subcriber_count_to_int(channel_info["subscribers"]["simpleText"])
                    preview_link = video["thumbnails"][0]["url"] if len(video["thumbnails"]) > 0 else ""
                    channel_logo_link = channel_info["thumbnails"][0]["url"] if len(channel_info["thumbnails"]) > 0 else ""
                    video_duration_td = YoutubeGrepEngine.duration_to_timedelta(video["duration"])
                    video_duration = timedelta_to_str(video_duration_td) if video_duration_td is not None else video["duration"]
                    result.append(
                        make_result_row(video["title"], video["publishedTime"], video_duration, 
                            views, video["link"], channel_info["title"], channel_info["url"], channel_subscribers,
                            channel_views, channel_info["joinedDate"], preview_link, channel_logo_link, video_info["keywords"],
                            video_duration_td))
                    counter = counter + 1
                    if counter == self._request_limit:
                        break
                if counter == self._request_limit:
                    break
                has_next_page = videos_search.next()
            self._model.setData(result)
            self._model.set_sort_cast(ResultFields.VideoPublishedTime, YoutubeGrepEngine.published_time_sort_cast)
            return True
        except Exception as _:
            self.error = traceback.format_exc() 
            return False
        
    @staticmethod
    def duration_to_timedelta(duration: str):
        if not duration:
            return None
        parts = duration.split(":")
        if len(parts) <= 1 or len(parts) > 3:
            return None
        parts.reverse()
        if len(parts) >= 2:
            seconds = int(parts[0])
            seconds = seconds + int(parts[1]) * 60
        if len(parts) >= 3:
            seconds = seconds + int(parts[2]) * 3600
        return timedelta(seconds=seconds)

    @staticmethod
    def published_time_to_timedelta(published_time: str):
        if not published_time:
            return None
        published_time = published_time.replace("Streamed ", "")
        number = int(published_time.split(" ")[0])
        if "day" in published_time:
            return timedelta(days=number)
        elif "week" in published_time:
            return timedelta(days=(number * 7))
        elif "month" in published_time:
            return timedelta(days=(number * 30))
        elif "year" in published_time:
            return timedelta(days=(number * 360))
        elif "hour" in published_time:
            return timedelta(hours=number)
        elif "min" in published_time:
            return timedelta(minutes=number)
        elif "sec" in published_time:
            return timedelta(seconds=number)
        return None

    @staticmethod
    def published_time_sort_cast(published_time: str):
        pb_timedelta = timedelta_to_str(YoutubeGrepEngine.published_time_to_timedelta(published_time))
        if pb_timedelta == "":
            return None
        return float(pb_timedelta.replace(":", ""))

    def _create_video_searcher(self, request_text: str):
        return VideosSearch(request_text, limit=self._request_limit)

    def _get_video_info(self, video_id: str):
        return Video.getInfo(video_id)

    def _get_channel_info(self, channel_id: str):
        return Channel.get(channel_id)


class YoutubeApiEngine(AbstractYoutubeEngine):
    def __init__(self, model: ResultTableModel, request_limit: int, api_key: str):
        super().__init__(model, request_limit)
        self._api_key = api_key

    def search(self, request_text: str):
        api_service_name = "youtube"
        api_version = "v3"

        try:
            youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = self._api_key)

            request = youtube.search().list(
                part = "snippet",
                maxResults = self._request_limit,
                q = request_text,
                type="video"
            )

            search_response = request.execute()

            video_ids = ""
            channel_ids = ""
            for search_item in search_response["items"]:
                video_ids = video_ids + "," + search_item["id"]["videoId"]
                channel_id = search_item["snippet"]["channelId"]
                if channel_id in channel_ids:
                    continue
                channel_ids = channel_ids + "," + channel_id
            video_ids = video_ids[1:] # Remove first comma
            channel_ids = channel_ids[1:] # Remove first comma

            video_request = youtube.videos().list(
                part = "contentDetails,statistics,snippet",
                id = video_ids
            )
            video_response = video_request.execute()

            channel_request = youtube.channels().list(
                part="snippet,statistics",
                id=channel_ids
            )
            channel_response = channel_request.execute()
            channels = {}
            for channel_item in channel_response["items"]:
                channels[channel_item["id"]] = channel_item

            result = []
            count = 0
            for search_item in search_response["items"]:
                video_item = video_response["items"][count]
                search_snippet = search_item["snippet"]
                content_details = video_item["contentDetails"]
                statistics = video_item["statistics"]
                video_title = search_snippet["title"]
                video_published_time = str(datetime.strptime(search_snippet["publishTime"], "%Y-%m-%dT%H:%M:%SZ"))
                video_duration_td = timedelta(seconds=isodate.parse_duration(content_details["duration"]).total_seconds())
                video_duration = timedelta_to_str(video_duration_td)
                views = int(statistics["viewCount"])
                video_link = "https://www.youtube.com/watch?v=" + search_item["id"]["videoId"]
                channel_title = search_snippet["channelTitle"]
                channel_url = "https://www.youtube.com/channel/" + search_snippet["channelId"]
                channel_item = channels[search_snippet["channelId"]]
                channel_subscribers = int(channel_item["statistics"]["subscriberCount"])
                channel_views = int(channel_item["statistics"]["viewCount"])
                channel_joined_date = ""
                video_preview_link = search_snippet["thumbnails"]["high"]["url"]
                channel_snippet = channel_item["snippet"]
                channel_logo_link = channel_snippet["thumbnails"]["default"]["url"]
                channel_logo_link = channel_logo_link.replace("https", "http") # https not working. I don't know why (2024.03.10)
                video_snippet = video_item["snippet"]
                tags = video_snippet["tags"] if "tags" in video_snippet else None
                count = count + 1
                result.append(
                    make_result_row(video_title, video_published_time, video_duration, views, 
                                    video_link, channel_title, channel_url, channel_subscribers,
                                    channel_views, channel_joined_date, video_preview_link, channel_logo_link, tags,
                                    video_duration_td))

            self._model.setData(result)
            return True
        except Exception as e:
            self.error = str(e)
            return False
