import traceback
from youtubesearchpython import (
    VideosSearch, 
    Channel
)
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
