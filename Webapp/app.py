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
from collections import Counter

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
country_capital = "Datasets/country.txt"
country_code = "Datasets/country-code.csv"

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
    counter = Counter(country_list)
    most_common_element = counter.most_common()
    most_common_string = most_common_element[0][0]
    for i in token_list:
        location = geocoder.osm(i)
        if location.ok:
            if location.raw['addresstype'] != 'state':
                if location.raw['address']['country'] == most_common_string:
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
        click_here = f' <a href="https://www.booking.com/searchresults.en-us.html?ss={coord[0].replace(" ", "+")}" target="_blank"> Go to Booking.com for a room! </a>'
        booking_html = pd.DataFrame([{coord[0], f'Want to book a hotel at {coord[0]}?{click_here}'}]).to_html(escape=False, index=False)
        print(click_here)

        myframe = folium.IFrame(booking_html, width=400, height=120)
        popup = folium.Popup(myframe, min_width=500, min_height=100)
        folium.Marker([coord[1], coord[2]], popup=popup).add_to(mymap)
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