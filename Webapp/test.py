import spacy
from pytube import YouTube

nlp = spacy.load("en_core_web_sm")  # Make sure to use an appropriate Spacy model

def GPE_extract(title):
    tokens = nlp(title)
    token_list = []
    for token in tokens.ents:
        if token.label_ == "GPE" or token.label_ == "LOC":
            if token.text.strip() not in token_list:
                token_list.append(token.text.strip())
    return token_list


def get_video_title(youtube_url):
    try:
        # Create a YouTube object
        yt = YouTube(youtube_url)

        # Get the title of the video
        title = yt.title

        return title

    except Exception as e:
        print(f"Error: {e}")
        return None

# Assuming get_video_title function is defined elsewhere and works correctly
youtube_url = "https://www.youtube.com/watch?v=N8bHCHl8X_0&ab_channel=Expedia"
video_title = get_video_title(youtube_url)

if video_title:
    print(f"The title of the video is: {video_title}")
    locations = GPE_extract(video_title)
    if locations:
        print(f"Locations mentioned in the title: {locations}")
    else:
        print("No locations found in the title.")
else:
    print("Failed to retrieve the video title.")