from fuzzywuzzy import process
from tqdm import tqdm
import pandas as pd
import requests
import sqlite3
from playwright.sync_api import sync_playwright

def load_city_names():
    print("Loading city names...")
    city_df = pd.read_csv("world_cities_major.csv", keep_default_na=False, encoding='utf_8')[['city','country','iso2']]
    city_country = (city_df['city']+','+city_df['country'])
    print("City names loaded.")
    return city_df, city_country

def load_hotels(filename:str):
    print("Loading hotels...")
    df = pd.read_csv(filename, keep_default_na=False, encoding='utf_8').drop_duplicates(subset=['city','hotel'],keep='last',ignore_index=True)
    try:
        df.drop('Unnamed: 0', axis=1,inplace=True)
    except:
        pass
    #cities_to_drop = df[df['hotel'].str.contains("\?", na=False)]['city'].unique()
    #df = df[~df['city'].isin(cities_to_drop)]
    print("Hotels loaded.")
    return df

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

def correct_city_names(df, city_country):
    print("Correcting city names...")
    mask = df['city'].apply(lambda x: '?' in x or '�' in x)
    df.loc[mask, 'city'] = df.loc[mask, 'city'].apply(lambda x: correct_city_name(x, city_country))
    print("City names corrected.")
    return df

def generate_urls(df):
    modified = 0
    failed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        for i in tqdm(range(10000,40000), desc="Generating URLs"):
            hotel = df.loc[i, 'hotel']
            if ('No Avaliable Hotel' not in hotel):
                if('Page Not Found' in requests.get(df.loc[i, 'url']).text):
                        s = hotel.replace(" ","+")+"+"+df.loc[i, "city"]
                        page = browser.new_page()
                        page.goto(f'https://www.booking.com/searchresults.en-us.html?ss={s}',timeout=120000)
                        try:
                            hotel = page.locator('//div[@data-testid="property-card"]').all()[0]
                            url = hotel.locator('//a[@data-testid="title-link"]').get_attribute('href').split('?')[0]
                            modified += 1
                        except:
                            url = f'https://www.booking.com/searchresults.en-us.html?ss={s}'
                            failed += 1
                        page.close()
                        df.loc[i, 'url'] = url
            if i % 100 == 1:
                pd.DataFrame(df).to_csv('hotel_cleaning.csv',index=False)
        browser.close()
    print(f"{modified} URLs generated. {failed} URLs failed.")
    return df

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
    #df1 = load_hotels("hotels(0, 10000).csv")
    #final = correct_city_names(final, city_country)
    #df2 = load_hotels("hotels(12000, 14000).csv")
    #final = pd.concat([pd.read_csv("hotels(0, 10000).csv", keep_default_na=False, encoding='utf_8'),pd.read_csv("hotels(12000, 14000).csv", keep_default_na=False, encoding='utf_8')],ignore_index=True)
    
    final = pd.read_csv("hotels_cleaned.csv", keep_default_na=False, encoding='utf_8').drop_duplicates(ignore_index=True)
    #final = generate_urls(final)

    save_to_csv(final,"hotels_cleaned.csv")
    save_to_sql(final,'hotels.db','hotels')
    print("Done!")

if __name__ == "__main__":
    main()
