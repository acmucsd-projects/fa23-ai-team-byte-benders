#test
import requests
import youtube_transcript_api
url = "https://www.youtube.com/watch?v=wVnimcQsuwk&t=2s"
url2 = "https://www.youtube.com/watch?v=wVnimcQsuw3"
youtube_id = url.split("=")[1][:11]
print(youtube_id)

#print(requests.get(url).text)
print("==============================================================")
print("This video isn't available anymore" in requests.get(url2).text)