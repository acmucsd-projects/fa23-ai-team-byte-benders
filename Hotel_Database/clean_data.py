from fuzzywuzzy import process
from tqdm import tqdm
import pandas as pd
import string
from unidecode import unidecode
import sqlite3

def load_city_names():
    print("Loading city names...")
    city_df = pd.read_csv("world_cities_major.csv", keep_default_na=False, encoding='utf_8')[['city','country','iso2']]
    city_country = (city_df['city']+','+city_df['country'])
    print("City names loaded.")
    return city_df, city_country

def load_hotels(filename:str):
    print("Loading hotels...")
    final = pd.read_csv(filename, keep_default_na=False, encoding='utf_8').drop_duplicates(subset=['city','hotel'],keep='last',ignore_index=True)
    try:
        final.drop('Unnamed: 0', axis=1,inplace=True)
        final.drop('Unnamed: 1', axis=1,inplace=True)
    except:
        pass
    cities_to_drop = final[final['hotel'].str.contains("\?", na=False)]['city'].unique()
    final = final[~final['city'].isin(cities_to_drop)]
    print("Hotels loaded.")
    return final

def correct_city_name(city, city_country):
    if ',' in city:
        clean_city = city.replace('?','').replace('�','')
        temp = city_country[city_country.str.contains(clean_city.split(',')[1].replace("+"," "))]
        match = process.extractOne(clean_city, temp)
        if match is not None:
            return match[0]
        else:
            print('no match found for ' + city + " with " + clean_city.split(',')[1])
            return city
    return city

def correct_city_names(final, city_country):
    print("Correcting city names...")
    mask = final['city'].apply(lambda x: '?' in x or '�' in x)
    final.loc[mask, 'city'] = final.loc[mask, 'city'].apply(lambda x: correct_city_name(x, city_country))
    print("City names corrected.")
    return final

def generate_urls(final, city_df):
    print("Generating URLs...")
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
    print("URLs generated.")
    return final

def save_to_csv(df,name):
    print("Saving to CSV...")
    pd.DataFrame(df).to_csv(name,index=False)
    print('number of cities: '+str(len(df['city'].unique())))
    print("Saved to CSV.")

def save_to_sql(df: pd.DataFrame, db_name: str, table_name: str):
    print("Saving to SQL...")
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print("Saved to SQL. Remember to put it under the Webapp/Datasets folder!")

def main():
    #city_df, city_country = load_city_names()
    final = load_hotels("hotels(0, 10000).csv")
    #final = correct_city_names(final, city_country)
    #final = generate_urls(final, city_df)
    save_to_csv(final,"hotels_cleaned.csv")
    save_to_sql(final,'hotels.db','hotels')
    print("Done!")

if __name__ == "__main__":
    main()
