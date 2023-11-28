from flask import Flask, render_template, request
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
from geopy import geocoders
import geocoder
import folium
import requests
from playwright.sync_api import sync_playwright
import datetime
import pandas as pd
import re

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
country_capital = "country.txt"
country_code = "country-code.csv"

with open(country_capital, 'r') as file:
    countries = [line.replace('\n', "").lower() for line in file]

code_df = pd.read_csv(country_code)
two_code_list = code_df['Alpha-2 code'].str.lower().to_list()
three_code_list = code_df['Alpha-3 code'].str.lower().to_list()


def GPE_extract(text):
    tokens = nlp(text)
    token_list = []
    for token in tokens.ents:
        if token.label_ == "GPE":                
            gpe = token.text.strip()
            gpe = gpe.replace("the", "")
            gpe = gpe.replace("'s", "")
            gpe = gpe.replace(".", "")
            gpe = gpe.strip()
            gpe = gpe.title()
            if gpe not in token_list:
                if (gpe.lower() not in countries) and (gpe.lower() not in three_code_list) and (gpe.lower() not in two_code_list):
                    token_list.append(gpe)
    return token_list

def get_coordinates(token_list):
    coord_list = []
    country_list = []
    for i in token_list:
        location = geocoder.osm(i)
        if location.ok:
            country_list += [location.raw['address']['country']]
            if location.raw['addresstype'] != 'state':
                latitude, longitude = location.latlng
                coord_list += [(i, latitude, longitude)]
        else:
            print("Error: " + i)
    return coord_list

def plot_points(coord_list):
    if (len(coord_list) == 0):
       map_center = [0,0]
    else:
       map_center = [sum(p[1] for p in coord_list) / len(coord_list), sum(p[2] for p in coord_list) / len(coord_list)]
    mymap = folium.Map(location=map_center, zoom_start=4)
    for coord in coord_list:
      folium.Marker([coord[1], coord[2]], popup=coord[0]).add_to(mymap)
    return mymap


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/hotel', methods=['GET', 'POST'])
def hotel():
    if request.method == "POST":
        url = request.form.get('youtube_url')
        if ("youtube.com/watch" not in url) or ("This video isn't available anymore" in requests.get(url).text):
            print("Invalid Link:" + url)
            return render_template('error.html')
    youtube_id = url.split("=")[1]  
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
        transcript_text = ""
        for line in transcript:
            transcript_text += " " + line['text'].replace("\n"," ")
        location_list = GPE_extract(transcript_text)
        coord_list = (get_coordinates(location_list))
        map = plot_points(coord_list)
        map.save("templates/map.html")
    except:
        return render_template("error.html")
    

    return render_template("hotel.html")

@app.route('/map',methods=['GET', 'POST'])
def map():  
    return render_template('map.html')


if __name__ == '__main__':
    app.run(debug=True)