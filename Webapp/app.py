from flask import Flask, render_template, request, g
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
import geocoder
import folium
import requests
import pandas as pd
import sqlite3
from collections import Counter
from webscrape_hotel import search_hotel # Optional

app = Flask(__name__)

nlp = spacy.load('en_core_web_sm')
country_capital = "Datasets/country.txt"
country_code = "Datasets/country-code.csv"
hotel_database = 'Datasets/hotels.db'

with open(country_capital, 'r') as file:
    countries = [line.replace('\n', "").lower() for line in file]

code_df = pd.read_csv(country_code, keep_default_na=False)
two_code_list = code_df['Alpha-2 code'].str.lower().to_list()
three_code_list = code_df['Alpha-3 code'].str.lower().to_list()

def get_hotel(city: str, country: str):
    city_country = (city+','+country).replace(' ','+')
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(hotel_database)
    c = db.cursor() # Query the database
    c.execute(f"SELECT * FROM hotels WHERE city = '{city_country}'")
    hotels = c.fetchall()
    if hotels:
        html = [f"<html>\n<body>\n<h1>Hotels at {city}</h1>\n<table border='1'>\n<tr><th>Hotel</th><th>Price</th><th>Score</th><th>Review Count</th><th>URL</th></tr>\n"]
        for hotel in hotels:
            html.append(f"<tr><td>{hotel[1]}</td><td>{hotel[2]}</td><td>{hotel[3]}</td><td>{hotel[4]}</td><td><a href='{hotel[5]}' target='_blank'>Link</a></td></tr>\n")
        html.append("</table>\n</body>\n</html>")
    else:
        pd.DataFrame(search_hotel(city_country, code_df[code_df['Name'].str.contains(country, case=False)].iloc[0, 1])).to_sql('hotels', db, if_exists='append', index=False) # Optional
        html = [f"<html>\n<body>\n<table border='1'>\n<tr><th>Want to book a hotel at {city}?</th><th><a href='https://www.booking.com/searchresults.en-us.html?ss={city_country}' target='_blank'> Go to Booking.com to find a hotel! </a></th></tr>\n"]
        html.append("</table>\n</body>\n</html>")
    return ''.join(html)

def GPE_extract(text):
    tokens = nlp(text)
    token_list = []
    for token in tokens.ents:
        if token.label_ == "GPE":
            gpe = token.text.strip()
            gpe = gpe.replace("the", "").replace("'s", "").replace(".", "")
            gpe = gpe.strip().title()
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
                    coord_list += [(i, latitude, longitude,location.raw['address']['country'])]
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
        booking_html = get_hotel(coord[0],coord[3])
        myframe = folium.IFrame(html=booking_html, width=600, height=150)
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
        if ("youtube.com/watch" not in url and "youtu.be/" not in url):
            print("Invalid Link:" + url)
            return render_template('error.html')
        if ("This video isn't available anymore" in requests.get(url).text):
            print("Invalid Video:" + url)
            return render_template('error.html')

    #try:
        if "youtu.be/" in url:
            youtube_id = url.split('tu.be/')[1].split("?")[0]
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
    #except:
        #return render_template("error.html")

    getattr(g, '_database', None).close()
    return render_template("hotel.html")

@app.route('/map',methods=['GET', 'POST'])
def map():  
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True)