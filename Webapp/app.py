from flask import Flask, render_template, request
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
from geopy import geocoders
import geocoder
import folium
import requests

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
           coord_list += [(i, latitude, longitude)]
        else:
           print("Error: " + i)
    return coord_list

def plot_points(coord_list):
    map_center = [sum(p[1] for p in coord_list) / len(coord_list), sum(p[2] for p in coord_list) / len(coord_list)]
    mymap = folium.Map(location=map_center, zoom_start=4)
    for coord in coord_list:
      folium.Marker([coord[1], coord[2]], popup=coord[0]).add_to(mymap)
    return mymap

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST' or request.method=='GET':
        url = request.form.get('youtube_url', '')
        if ("youtube.com/watch?v=" not in url) or ("This video isn't available anymore" in requests.get(url).text):
           print("Invalid Link")
        else:
            youtube_id = url.split("=")[1]           
            transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
            transcript_text = ""
            for line in transcript:
                transcript_text += " " + line['text'].replace("\n"," ")
            location_list = GPE_extract(transcript_text)
            coord_list = (get_coordinates(location_list))
            map = plot_points(coord_list)
            map.save("templates/map.html")
    return render_template('home.html')

@app.route('/map')
def map():
   return render_template('map.html')
   
if __name__ == '__main__':
    app.run(debug=False)

