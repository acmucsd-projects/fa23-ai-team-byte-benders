from flask import Flask, render_template, request, g
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
import geocoder
import folium
import pandas as pd
import time, re, sqlite3
from collections import Counter
from webscrape_hotel import search_hotel

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
non_alphanumeric = re.compile("[^A-Za-z0-9&/\()-+'_., ]")

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
    coord_start = time.time()
    coord_list = []
    country_list = []
    location_list = []
    translated_dict = {}

    for i in token_list:
        location = geocoder.osm(i)
        if location.ok:
            country = location.raw['address']['country']
            if (bool(re.search(non_alphanumeric, country))):
                if country not in translated_dict:
                    translated_dict[country] = country #translator deleted for running on local env
                country = translated_dict[country]
            location_list.append((i,location,country))
            country_list += [country]
    counter = Counter(country_list)
    most_common_element = counter.most_common()
    if len(counter) > 4:
        other_common = counter.most_common(len(counter)//2-1)
    else:
        other_common = []
    for loc in location_list:
        location = loc[1]
        if location.raw['addresstype'] != 'state':
            if loc[2] == most_common_element[0][0] or loc[2] in [country for country, _ in other_common]:
                latitude, longitude = location.latlng
                coord_list += [(loc[0], latitude, longitude, loc[2])]

    print(f"Coordinates took {round((time.time() - coord_start)*1000)} ms.")
    return coord_list

def plot_points(coord_list):
    pp_start = time.time()
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
    print(f"All hotel pins took {round((time.time() - pp_start)*1000)} ms.")
    return mymap
    
def get_hotel(city: str, country: str):
    city_country = (city+','+country).replace(' ','+')
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(hotel_database)
    c = db.cursor() # Query the database
    c.execute("SELECT * FROM hotels WHERE city = ?", (city_country,))
    hotels = c.fetchall()
    if not hotels: #Optional
        hotel_list = search_hotel(city_country)
        pd.DataFrame(hotel_list).to_sql('hotels', db, if_exists='append', index=False)
        hotels = [tuple(d.values()) for d in hotel_list]
    if hotels[0][1] == 'No Avaliable Hotel' or not hotels:
        html = [f"<html>\n<body>\n<table border='1'>\n<tr><th>Want to book a hotel at {city}?</th><th><a href='https://www.booking.com/searchresults.en-us.html?ss={city_country}' target='_blank'> Go to Booking.com to find a hotel! </a></th></tr>\n"]
        html.append("</table>\n</body>\n</html>")
    else:
        html = [f"<html>\n<body>\n<h1>Hotels at {city}</h1>\n<table border='1'>\n<tr><th>Hotel</th><th>Price</th><th>Score</th><th>Review Count</th><th>URL</th></tr>\n"]
        for hotel in hotels:
            html.append(f"<tr><td>{hotel[1]}</td><td>{hotel[2]}</td><td>{hotel[3]}</td><td>{hotel[4]}</td><td><a href='{hotel[5]}' target='_blank'>Link</a></td></tr>\n")
        html.append("</table>\n</body>\n</html>")
    return ''.join(html)

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index1.html')

@app.route('/hotel', methods=['GET', 'POST'])
def hotel():
    request_start = time.time()
    if request.method == "POST":
        url = request.form.get('youtube_url')
        if ("youtube.com/watch" not in url and "youtu.be/" not in url):
            print("Invalid Link:" + url)
            return render_template('error.html')

    try:
        if "youtu.be/" in url:
            youtube_id = url.split('tu.be/')[1].split("?")[0]
        else:
            youtube_id = url.split("=")[1]

        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
        transcript_text = ""
        for line in transcript:
            transcript_text += " " + line['text'].replace("\n"," ")
        print(f"Transcropt took {round((time.time() - request_start)*1000)} ms.")
        location_list = GPE_extract(transcript_text)
        coord_list = (get_coordinates(location_list))
        map = plot_points(coord_list)
        map.save("templates/map.html")
    except:
        return render_template("error.html")
    
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    print(f"request took {round((time.time() - request_start), 3)} seconds.")
    return render_template("hotel.html")

@app.route('/map',methods=['GET', 'POST'])
def map():  
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True,host='127.0.0.1',port=8080)