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
import string

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


def get_coordinates(token_list):
    coord_list = []
    for i in token_list:
        location = geocoder.osm(i)
        if location.ok:
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

def get_hotel(city, browser):
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
    
        city = city.replace(" ", "+")
        
        # IMPORTANT: dates must be future dates, otherwise it won't work
        checkin_date = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        checkout_date = (datetime.date.today() + datetime.timedelta(days=31)).strftime("%Y-%m-%d")
        
        page = browser.new_page()
        hotel_list = []

        page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'.replace("{checkin_date}",checkin_date).replace("{checkout_date}",checkout_date).replace("{city}", city)

        try:
            page.goto(page_url, timeout=10000)
        except:
            print("get hotel page failed.")
            return []

        hotels = page.locator('//div[@data-testid="property-card"]').all()
        print(f'There are {len(hotel_list)} hotels.')
    
        count = 0

        for hotel in hotels:
            if (count == 3):
                break
            hotel_dict = {}
            try:
                hotel_dict['hotel'] = hotel.locator('//div[@data-testid="title"]').inner_text()
                hotel_dict['price'] = hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
                #hotel_dict['score'] = hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
                #hotel_dict['avg review'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
                #hotel_dict['reviews count'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text().split()[0]

                hotel_string = hotel_dict['hotel'].translate(str.maketrans("", "", string.punctuation)).replace("  "," ").replace(" ", "+")
                hotel_dict['url'] = f'www.booking.com/searchresults.html?ss={hotel_string}'

                hotel_list.append(hotel_dict)
                count += 1
            except:
                print("get hotel failed.")

        browser.close()

    return hotel_list

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
    transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
    transcript_text = ""
    for line in transcript:
        transcript_text += " " + line['text'].replace("\n"," ")
    location_list = GPE_extract(transcript_text)
    coord_list = (get_coordinates(location_list))
    map = plot_points(coord_list)
    map.save("templates/map.html")

    return render_template("hotel.html")

@app.route('/map',methods=['GET', 'POST'])
def map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=False)