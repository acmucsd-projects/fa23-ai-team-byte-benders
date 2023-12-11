from fuzzywuzzy import process
from tqdm import tqdm
import pandas as pd
import string
from unidecode import unidecode

# Load the correct city names
city_df = pd.read_csv("world_cities_major.csv", keep_default_na=False, encoding='utf_8')[['city','country','iso2']]
city_country = (city_df['city']+','+city_df['country'])
def correct_city_name(city):
    # Check if city name contains a comma
    if ',' in city:
        clean_city = city.replace('?','').replace('�','')
        # Find the closest match in correct_cities_df
        temp = city_country[city_country.str.contains(clean_city.split(',')[1].replace("+"," "))]
        match = process.extractOne(clean_city, temp)
        
        # If the match is close enough
        if match is not None:
            return match[0]
        else:
            print('no match found for ' + city + " with " + clean_city.split(',')[1])
            return city
    return city

df1 = pd.read_csv("hotels(0, 10000).csv", keep_default_na=False, encoding='utf_8')
final = df1

cities_to_drop = final[final['hotel'].str.contains("\?", na=False)]['city'].unique()

final = final[~final['city'].isin(cities_to_drop)]

# Create a mask for rows where city name contains '?' or '�'
mask = final['city'].apply(lambda x: '?' in x or '�' in x)

# Apply the correct_city_name function to the city names where mask is True
final.loc[mask, 'city'] = final.loc[mask, 'city'].apply(correct_city_name)

for i in tqdm(final.index, desc="Generating URLs"):
    hotel = final.loc[i, 'hotel']
    if ('No Avaliable Hotel' not in hotel):
        try:
            hotel_string = unidecode(hotel.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation)))).replace("  "," ").replace("   "," ").replace("    "," ").replace(" ", "-").replace("--", "-").replace("--", "-").lower()
            cc = city_df.loc[city_df['country'] == final.loc[i, 'city'].split(',')[1].replace("+"," ")].iloc[:, 2].values[0].lower()
        except:
            print("Error occured with: " + final.loc[i, 'city'] + " and " + hotel_string)            
        url = f'https://www.booking.com/hotel/{cc}/{hotel_string}'
        if not url.endswith('.html'):
               url += '.html'
        final.loc[i, 'url'] = url


pd.DataFrame(final).to_csv("hotels_cleaned.csv",index=False)
print('number of cities: '+str(len(final['city'].unique())))

for city in final['city'].unique():
    if ('?' in city):
        print(city)