import csv
from youtubesearchpython import VideosSearch, Channel

request_text = 'Механизаторы деревни'
request_limit = 30

videos_search = VideosSearch(request_text, limit = request_limit)

with open('result.csv', 'w', newline='', encoding='utf-8') as csvfile:
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
            channel = Channel.get(video['channel']['id'])
            csv_writer.writerow([video['title'], video['publishedTime'], video['duration'], 
                                video['viewCount']['text'], video['link'],
                                channel['title'], channel['url'], channel['subscribers']['simpleText'],
                                channel['views'], channel['joinedDate']])
            counter = counter + 1
            if counter == request_limit:
                break
        if counter == request_limit:
                break
        has_next_page = videos_search.next()
