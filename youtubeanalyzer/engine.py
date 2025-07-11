from datetime import datetime, timedelta
import traceback
import isodate
from PySide6.QtCore import (
    QObject,
    Signal,
    QUrl,
    QJsonDocument,
    QTimer
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
from youtubeanalyzer.model import (
    PublishedDateFormat,
    make_result_row,
    ResultFields,
    ResultTableModel,
    DataCache,
    VideoCategory
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
        url = reply.url()
        if image.isNull() and self._try_again:
            self._manager.get(QNetworkRequest(url))
            self._try_again = False
        self._try_again = True
        self._data_cache.cache_image(url.toString(), image)
        self.finished.emit(image)


class SearchAutocompleteDownloader(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._handle_finished)
        self._data = []
        self._delay_timer = QTimer()
        self._delay_timer.setSingleShot(True)
        self._delay_timer.setInterval(200)
        self._delay_timer.timeout.connect(lambda: self.start_download(self._delayed_query))
        self._delayed_query = ""

    def start_download(self, query: str):
        url = "http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q=" + query
        self._data.clear()
        self._manager.clearConnectionCache()
        self._manager.get(QNetworkRequest(url))

    def start_download_delayed(self, query: str):
        self._delayed_query = query
        self._delay_timer.start()

    def _handle_finished(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            self.error.emit(reply.errorString())
            return
        json = QJsonDocument.fromJson(reply.readAll())
        if not json.isArray():
            self.error.emit("Reply is not JSON array")
            return

        json_array = json.array()
        if json_array.size() < 2:
            self.error.emit("JSON array has incompatible size")
            return

        autocomplete_json_array = json_array.at(1).toArray()
        for i in range(autocomplete_json_array.size()):
            self._data.append(autocomplete_json_array.at(i).toString())
        self.finished.emit(self._data)


class AbstractYoutubeEngine:
    def __init__(self, model: ResultTableModel = None, request_limit: int = 10, results_per_page: int = 10,
                 request_timeout_sec: int = 10):
        self.errorDetails = None
        self.errorReason = None
        self._model = model
        self._request_limit = request_limit
        self._results_per_page = min(request_limit, results_per_page)
        self._request_timeout_sec = request_timeout_sec

    def set_request_timeout_sec(self, value_sec: int):
        self._request_timeout_sec = value_sec

    def search(self, request_text: str):
        raise "AbstractYoutubeEngine.search is not implemented"

    def get_video_categories(self):
        raise "AbstractYoutubeEngine.get_video_categories is not implemented"

    def trends(self, category_id: int, region_code: str = "US"):
        raise "AbstractYoutubeEngine.trends is not implemented"


class YoutubeGrepEngine(AbstractYoutubeEngine):
    def __init__(self, model: ResultTableModel, request_limit: int):
        super().__init__(model, request_limit)

    def search(self, request_text: str):
        self.errorDetails = None
        self.errorReason = None
        try:
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
                    video_duration_d = YoutubeGrepEngine.duration_to_timedelta(video["duration"])
                    video_duration = timedelta_to_str(video_duration_d)
                    result.append(
                        make_result_row(
                            video["title"], video["publishedTime"], video_duration,
                            views, video["link"], channel_info["title"], channel_info["url"],
                            channel_subscribers, channel_views, channel_info["joinedDate"], preview_link, channel_logo_link,
                            video_info["keywords"], video_duration_d, counter, video["type"]))
                    counter = counter + 1
                    if counter == self._request_limit:
                        break
                if counter == self._request_limit:
                    break
                has_next_page = videos_search.next()
            self._model.set_data(result)
            self._model.set_sort_cast(ResultFields.VideoPublishedTime, YoutubeGrepEngine.published_time_sort_cast)
            return True
        except Exception as exc:
            print(exc)
            self.errorDetails = traceback.format_exc()
            return False

    def get_video_categories(self, region_code: str = "US", output_language="en_US"):
        self.errorDetails = "YoutubeGrepEngine doesn't support video categories"
        self.errorReason = "Not supported"
        return []

    def trends(self, category_id: int, region_code: str = "US"):
        self.errorDetails = "YoutubeGrepEngine doesn't support trends"
        self.errorReason = "Not supported"
        return False

    @staticmethod
    def duration_to_timedelta(duration: str):
        if not duration:
            return timedelta(seconds=0)
        parts = duration.split(":")
        if len(parts) <= 1 or len(parts) > 3:
            return timedelta(seconds=0)
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
        return VideosSearch(request_text, limit=self._request_limit, timeout=self._request_timeout_sec)

    def _get_video_info(self, video_id: str):
        return Video.getInfo(video_id, timeout=self._request_timeout_sec)

    def _get_channel_info(self, channel_id: str):
        return Channel.get(channel_id)


class YoutubeApiEngine(AbstractYoutubeEngine):
    def __init__(self, api_key: str, model: ResultTableModel = None, request_limit: int = 10, results_per_page: int = 10):
        super().__init__(model, request_limit, results_per_page)
        self._api_key = api_key

    def search(self, request_text: str):
        self.errorDetails = None
        self.errorReason = None
        try:
            def request_handler(youtube, page_token):
                request = youtube.search().list(
                    part="snippet",
                    maxResults=self._results_per_page,
                    q=request_text,
                    type="video",
                    pageToken=page_token
                )
                return request.execute()

            def video_id_getter(item): return item["id"]["videoId"]

            result = self._request_videos(request_handler, video_id_getter, "publishTime")
            self._model.set_data(result)
            return True
        except Exception as e:
            self.errorDetails = str(e)
            return False

    def get_video_categories(self, region_code: str = "US", output_language="en_US"):
        self.errorDetails = None
        self.errorReason = None
        try:
            youtube = self._create_youtube_client()
            request = youtube.videoCategories().list(
                part="snippet",
                regionCode=region_code,
                hl=output_language
            )
            response = request.execute()
            categories = []
            for item in response["items"]:
                snippet = item["snippet"]
                categories.append(VideoCategory(item["id"], snippet["title"]))
            return categories
        except Exception as e:
            self.errorDetails = str(e)
            return []

    def trends(self, category_id: int, region_code: str = "US"):
        self.errorDetails = None
        self.errorReason = None
        try:
            def request_handler(youtube, page_token):
                request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    chart="mostPopular",
                    regionCode=region_code,
                    videoCategoryId=category_id,
                    maxResults=self._results_per_page,
                    pageToken=page_token
                )
                return request.execute()

            def video_id_getter(item): return item["id"]

            result = self._request_videos(request_handler, video_id_getter, "publishedAt")
            self._model.set_data(result)
            return True
        except Exception as e:
            if hasattr(e, "reason"):
                self.errorReason = e.reason
            self.errorDetails = str(e)
            return False

    def _create_youtube_client(self):
        api_service_name = "youtube"
        api_version = "v3"
        return googleapiclient.discovery.build(api_service_name, api_version, developerKey=self._api_key)

    def _request_videos(self, request_handler, video_id_getter, published_time_key):
        youtube = self._create_youtube_client()
        page_token = ""
        total_count = 0
        result = []

        while True:
            response = request_handler(youtube, page_token)

            video_response, channels = self._get_response_details(youtube, response, video_id_getter)

            count = 0
            for responce_item in response["items"]:
                result.append(self._responce_item_to_result(responce_item, video_response["items"][count], total_count,
                                                            channels, published_time_key, video_id_getter))
                count = count + 1
                total_count = total_count + 1

                if total_count >= self._request_limit:
                    break

            if total_count >= self._request_limit:
                break
            if "nextPageToken" not in response:
                break
            if response["nextPageToken"]:
                page_token = response["nextPageToken"]

        return result

    def _get_video_details(self, youtube, video_ids):
        video_request = youtube.videos().list(
            part="contentDetails,statistics,snippet",
            id=video_ids
        )
        return video_request.execute()

    def _get_channel_details(self, youtube, channel_ids):
        channel_request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_ids
        )
        return channel_request.execute()

    def _get_response_details(self, youtube, response, video_id_getter):
        video_ids = ""
        channel_ids = ""
        for item in response["items"]:
            video_ids = video_ids + "," + video_id_getter(item)
            channel_id = item["snippet"]["channelId"]
            if channel_id in channel_ids:
                continue
            channel_ids = channel_ids + "," + channel_id
        video_ids = video_ids[1:]  # Removing of the first comma
        channel_ids = channel_ids[1:]  # Removing of the first comma

        video_response = self._get_video_details(youtube, video_ids)
        channel_response = self._get_channel_details(youtube, channel_ids)
        channels = {}
        for channel_item in channel_response["items"]:
            channels[channel_item["id"]] = channel_item

        return video_response, channels

    def _type(self, vid):
        return "unknown"
        # The code below is not fast enough to use for a large number of videos in a request.
        # We can come back to video type detecting if we find a better method for doing so.
        # url = 'http://www.youtube.com/shorts/' + vid
        # ret = requests.get(url, timeout=100)
        # text = ret.text
        # urlshorts = "//www.youtube.com/shorts/"
        # if (text.find(urlshorts) > 0):
        #     type = "shorts"
        # else:
        #     type = "longs"
        # return type

    def _responce_item_to_result(self, responce_item, video_item, result_index, channels, publish_time_key, video_id_getter):
        search_snippet = responce_item["snippet"]
        content_details = video_item["contentDetails"]
        statistics = video_item["statistics"]
        video_title = search_snippet["title"]
        video_published_time = datetime.strptime(search_snippet[publish_time_key], "%Y-%m-%dT%H:%M:%SZ")
        video_published_time_str = video_published_time.strftime(PublishedDateFormat)
        video_duration_td = timedelta(seconds=isodate.parse_duration(content_details["duration"]).total_seconds())
        video_duration = timedelta_to_str(video_duration_td)
        views = int(statistics["viewCount"])
        video_link = "https://www.youtube.com/watch?v=" + video_id_getter(responce_item)
        channel_title = search_snippet["channelTitle"]
        channel_url = "https://www.youtube.com/channel/" + search_snippet["channelId"]
        channel_item = channels[search_snippet["channelId"]]
        channel_subscribers = int(channel_item["statistics"]["subscriberCount"])
        channel_views = int(channel_item["statistics"]["viewCount"])
        channel_joined_date = ""
        video_preview_link = search_snippet["thumbnails"]["high"]["url"]
        channel_snippet = channel_item["snippet"]
        channel_logo_link = channel_snippet["thumbnails"]["default"]["url"]
        channel_logo_link = channel_logo_link.replace("https", "http")  # https is not working. I don't know why
        video_snippet = video_item["snippet"]
        tags = video_snippet["tags"] if "tags" in video_snippet else None
        video_type = self._type(video_id_getter(responce_item))

        return make_result_row(video_title, video_published_time_str, video_duration, views,
                               video_link, channel_title, channel_url, channel_subscribers,
                               channel_views, channel_joined_date, video_preview_link, channel_logo_link, tags,
                               video_duration_td, result_index + 1, video_type)
