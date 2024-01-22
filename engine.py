import traceback
from youtubesearchpython import (
    VideosSearch, 
    Channel
)
import googleapiclient.discovery
from model import (
    make_result_row,
    ResultTableModel
)


def view_count_to_int(count_str):
    if not count_str:
        return 0
    parts = count_str.split()
    if len(parts) == 0:
        return 0
    processed_count = parts[0].replace(",", "")
    return int(processed_count) if processed_count.isdigit() else 0


def subcriber_count_to_int(count_str):
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
    return int(float(number_letter[:-1]) * multiplier)


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
            videos_search = VideosSearch(request_text, limit = self._request_limit)
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
                    result.append(
                        make_result_row(video["title"], video["publishedTime"], video["duration"], 
                            views, video["link"], channel["title"], channel["url"], channel_subscribers,
                            channel_views, channel["joinedDate"]))
                    counter = counter + 1
                    if counter == self._request_limit:
                        break
                if counter == self._request_limit:
                    break
                has_next_page = videos_search.next()
            self._model.setData(result)
            return True
        except Exception as _:
            self.error = traceback.format_exc() 
            return False


class YoutubeApiEngine(AbstractYoutubeEngine):
    def __init__(self, model: ResultTableModel, request_limit: int, api_key: str):
        super().__init__(model, request_limit)
        self._api_key = api_key

    def search(self, request_text: str):
        api_service_name = "youtube"
        api_version = "v3"

        youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = self._api_key)

        request = youtube.search().list(
            part = "snippet",
            maxResults = self._request_limit,
            q = request_text,
            type="video"
        )
        try:
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
                part = "contentDetails,statistics",
                id = video_ids
            )
            video_response = video_request.execute()

            channel_request = youtube.channels().list(
                part="statistics",
                id=channel_ids
            )
            channels = {}
            channel_response = channel_request.execute()
            for channel_item in channel_response["items"]:
                channels[channel_item["id"]] = channel_item

            result = []
            count = 0
            for search_item in search_response["items"]:
                video_item = video_response["items"][count]
                snippet = search_item["snippet"]
                channel_item = channels[snippet["channelId"]]
                content_details = video_item["contentDetails"]
                statistics = video_item["statistics"]
                video_title = snippet["title"]
                video_published_time = snippet["publishTime"]
                video_duration = content_details["duration"]
                views = int(statistics["viewCount"])
                video_link = "https://www.youtube.com/watch?v=" + search_item["id"]["videoId"]
                channel_title = snippet["channelTitle"]
                channel_url = ""
                channel_subscribers = int(channel_item["statistics"]["subscriberCount"])
                channel_views = int(channel_item["statistics"]["viewCount"])
                channel_joined_date = ""
                count = count + 1
                result.append(
                    make_result_row(video_title, video_published_time, video_duration, views, 
                                    video_link, channel_title, channel_url, channel_subscribers,
                                    channel_views, channel_joined_date))

            self._model.setData(result)
            return True
        except Exception as e:
            self.error = str(e)
            return False
