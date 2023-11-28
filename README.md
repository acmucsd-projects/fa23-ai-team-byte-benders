# fa23-ai-team-byte-benders
Welcome to the byte benders project! 

## Overview
Our goal is to develop a webapp that, given a youtube video url, returns a map with a pin on each location mentioned. 
This will simplify your itinerary-planning: no more googling places you heard from a video, our webapp will do it automatically!
In addition, when you clicl on a pin, you'll see a link directing you to [booking.com](https://www.booking.com/index.it.html?aid=397594&label=gog235jc-1DCAEoggI46AdIM1gDaIkCiAEBmAEUuAEHyAEM2AED6AEBiAIBqAIDuAKHopWrBsACAdICJDZiZWNhNzcyLTVmZWYtNGUyYi1hMDMzLWQ0MTg4YjRmMmY2MtgCBOACAQ&sid=0091c803ef3b597482296dcd12748d99&keep_landing=1&sb_price_type=total&), where you can find hotels for that destination. 

## The Project
(webapp link - to be added after deployment)  
(presentation link)

## App walk through
1. Paste a youtube video url into the input box in the home page
2. When you hit search, the backend will generate a transcript of the youtube video, analyze it using spacy to find any GPEs mentioned, and put them in a list
3. The list will be displayed on an interactive map using leaflet and folium. each pin is a location mentioned in the video
4. When clicking on each pin, a box will appear. The link displayed on the box is a connection to the booking.com page for the specific location.
   
## Technologies
- Spacy (NLP tool)
- Geopy (Geolocation)
- Leaflet/Folium (Interactive map)
- Flask (Webapp developemnt)
- Heroku (Webapp deployment)
  
## Challenges
. Disambiguation of location names: how does spacy know if the 'Venice' mentioned in the video is in Italy or California?

. Optimization of webapp and parallel processing: the tool is very slow as of right now; we are looking for a way to fasten it. 

. Misclassification of locations: sometimes, spacy misclassifies people's names (or other instances) with locations.

## Authors info
Olimpia Carrioli [LinkedIn link](https://www.linkedin.com/in/olimpia-carrioli-708192212/)  
Vishal Patel [LinkedIn link](https://www.linkedin.com/in/patvishal/)
