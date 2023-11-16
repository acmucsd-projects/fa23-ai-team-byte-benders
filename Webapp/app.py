from flask import Flask, render_template, request
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
from geopy import geocoders
import geocoder


app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')

def GPE_extract(text):
    tokens = nlp(text)
    token_list=[]
    for token in tokens.ents:
      if token.label_ == "GPE":
        if token.text.strip() not in token_list:
           token_list += [token.text.strip()]
    return token_list


def get_coordinates(token_lst):
    coord_list = []
    for i in token_lst:
        location = geocoder.osm(i)
        if location.ok:
           latitude, longitude = location.latlng
           coord_list += [{"Location": i, "Latitude": latitude, "Longitude": longitude}]
        else:
           print("Error: " + i)
    return coord_list

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('youtube_url', '')
        youtube_id = url.split("=")[1]
        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
        transcript_text = ""
        for line in transcript:
           transcript_text += " " + line['text'].replace("\n"," ")
        location_list = GPE_extract(transcript_text)
        print(get_coordinates(location_list))



    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=False)
