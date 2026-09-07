from datetime import datetime, timedelta
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
import googleapiclient.discovery
from youtubeanalyzer.model import (
    PublishedDateFormat,
    make_result_row,
    ResultTableModel,
    DataCache,
    VideoCategory
)


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
            reply.deleteLater()
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
        reply.deleteLater()


class FileDownloader(QObject):
    finished = Signal(QUrl, bytes)
    error = Signal(QUrl, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = QNetworkAccessManager()
        self._manager.finished.connect(self._handle_finished)

    def start_download(self, url: QUrl):
        self._manager.get(QNetworkRequest(url))

    def _handle_finished(self, reply: QNetworkReply):
        url = reply.url()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.error.emit(url, reply.errorString())
        else:
            self.finished.emit(url, bytes(reply.readAll()))
        reply.deleteLater()


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
        self.warnings = []
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


class YoutubeApiEngine(AbstractYoutubeEngine):
    def __init__(self, api_key: str, model: ResultTableModel = None, request_limit: int = 10, results_per_page: int = 10):
        super().__init__(model, request_limit, results_per_page)
        self._api_key = api_key

    def search(self, request_text: str):
        self.errorDetails = None
        self.errorReason = None
        self.warnings = []
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

            def video_id_getter(item):
                id_obj = item.get("id", {})
                return id_obj.get("videoId", None)

            result = self._request_videos(request_handler, video_id_getter, "publishTime")
            self._model.set_data(result)
            return True
        except Exception as e:
            self.errorDetails = str(e)
            return False

    def get_video_categories(self, region_code: str = "US", output_language="en_US"):
        self.errorDetails = None
        self.errorReason = None
        self.warnings = []
        try:
            youtube = self._create_youtube_client()
            request = youtube.videoCategories().list(
                part="snippet",
                regionCode=region_code,
                hl=output_language
            )
            response = request.execute()
            if "items" not in response:
                raise RuntimeError("The video categories response doesn't contain 'items'")
            categories = []
            for item in response["items"]:
                category_id = item.get("id")
                snippet = item.get("snippet")
                if not category_id or snippet is None:
                    self.warnings.append(
                        "A video category was skipped: the response item is missing 'id' or 'snippet'.")
                    continue
                categories.append(VideoCategory(category_id, snippet.get("title", "")))
            return categories
        except Exception as e:
            self.errorDetails = str(e)
            return []

    def trends(self, category_id: int, region_code: str = "US"):
        self.errorDetails = None
        self.errorReason = None
        self.warnings = []
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

            def video_id_getter(item): return item.get("id", None)

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
            if "items" not in response:
                # Without "items" there is nothing to work with at all - this page is unusable.
                raise RuntimeError("The API response doesn't contain 'items'")

            valid_items = self._filter_items_with_video_id(response["items"], video_id_getter)
            videos, channels = self._get_response_details(youtube, valid_items)

            for item, video_id in valid_items:
                video_item = videos.get(video_id)
                if video_item is None:
                    self.warnings.append(f"Video '{video_id}' was skipped: no details were returned for it.")
                    continue

                row = self._item_to_result(item, video_item, total_count, channels, published_time_key, video_id)
                if row is None:
                    continue

                result.append(row)
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

    def _filter_items_with_video_id(self, items, video_id_getter):
        # A missing video ID makes an item unusable: we can't fetch its details, nor build a link for it.
        valid_items = []
        for item in items:
            try:
                video_id = video_id_getter(item)
            except (KeyError, TypeError, AttributeError):
                video_id = None
            if not video_id:
                self.warnings.append("A video was skipped: its ID is missing in the response.")
                continue
            valid_items.append((item, video_id))
        return valid_items

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

    def _get_response_details(self, youtube, valid_items):
        video_ids = [video_id for _, video_id in valid_items]
        channel_ids = []
        for item, _ in valid_items:
            # A missing channelId is not fatal: the video is still shown, just without channel info.
            channel_id = item.get("snippet", {}).get("channelId")
            if channel_id and channel_id not in channel_ids:
                channel_ids.append(channel_id)

        videos = {}
        if video_ids:
            video_response = self._get_video_details(youtube, ",".join(video_ids))
            for video_item in video_response.get("items", []):
                video_id = video_item.get("id")
                if video_id:
                    videos[video_id] = video_item

        channels = {}
        if channel_ids:
            channel_response = self._get_channel_details(youtube, ",".join(channel_ids))
            for channel_item in channel_response.get("items", []):
                channel_id = channel_item.get("id")
                if channel_id:
                    channels[channel_id] = channel_item

        return videos, channels

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

    def _item_to_result(self, item, video_item, result_index, channels, publish_time_key, video_id):
        snippet = item.get("snippet")
        if snippet is None:
            # Without the snippet we'd lose the title, publish time, channel and thumbnail - not worth
            # showing an almost-empty row, so the whole video is skipped.
            self.warnings.append(f"Video '{video_id}' was skipped: the response item is missing 'snippet'.")
            return None

        content_details = video_item.get("contentDetails", {})
        statistics = video_item.get("statistics", {})
        video_snippet = video_item.get("snippet", {})

        video_title = snippet.get("title", "")

        published_time_raw = snippet.get(publish_time_key)
        if published_time_raw:
            video_published_time = datetime.strptime(published_time_raw, "%Y-%m-%dT%H:%M:%SZ")
            video_published_time_str = video_published_time.strftime(PublishedDateFormat)
        else:
            video_published_time_str = ""

        duration_raw = content_details.get("duration")
        video_duration_td = (
            timedelta(seconds=isodate.parse_duration(duration_raw).total_seconds())
            if duration_raw else timedelta(seconds=0)
        )
        video_duration = timedelta_to_str(video_duration_td)
        views = int(statistics.get("viewCount", 0))
        video_link = "https://www.youtube.com/watch?v=" + video_id
        channel_title = snippet.get("channelTitle", "")
        channel_id = snippet.get("channelId", "")
        channel_url = "https://www.youtube.com/channel/" + channel_id if channel_id else ""

        channel_item = channels.get(channel_id, {})
        channel_stats = channel_item.get("statistics", {})
        channel_subscribers = int(channel_stats.get("subscriberCount", 0))
        channel_views = int(channel_stats.get("viewCount", 0))
        channel_joined_date = ""

        video_preview_link = ""
        thumbnails = snippet.get("thumbnails", {})
        for size in ("medium", "high", "default"):
            if size in thumbnails:
                video_preview_link = thumbnails[size].get("url", "")
                break

        video_preview_sizes = [
            {"width": thumbnail.get("width", 0), "height": thumbnail.get("height", 0), "url": thumbnail["url"]}
            for thumbnail in thumbnails.values() if thumbnail.get("url")
        ]
        video_preview_sizes.sort(key=lambda thumbnail: thumbnail["width"])

        channel_logo_link = ""
        channel_snippet = channel_item.get("snippet", {})
        if channel_snippet:
            channel_thumbnails = channel_snippet.get("thumbnails", {})
            if "default" in channel_thumbnails:
                channel_logo_link = channel_thumbnails["default"]["url"]
                # https is not working. I don't know why
                channel_logo_link = channel_logo_link.replace("https", "http")

        tags = video_snippet.get("tags", [])
        video_type = self._type(video_id)

        return make_result_row(video_title, video_published_time_str, video_duration, views,
                               video_link, channel_title, channel_url, channel_subscribers,
                               channel_views, channel_joined_date, video_preview_link, channel_logo_link, tags,
                               video_duration_td, result_index + 1, video_type, video_preview_sizes)
