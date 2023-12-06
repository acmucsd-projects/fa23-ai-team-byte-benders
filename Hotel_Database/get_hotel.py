import asyncio
from playwright.async_api import async_playwright
import datetime
import pandas as pd
from tqdm.asyncio import tqdm
import string
import os

# import database(s)
city_list_short = pd.read_csv("world_cities_major.csv", keep_default_na=False)[['city','country','iso2']]

# configuration / parameters
exe_list = city_list_short
exe_range = (0, 10000)
get_score_and_reviews = True
hotels_per_city = 5
max_retries = 3
filename = f"hotels{str(exe_range)}.csv"
check_point_interval = 20 # save file after this number of cities

sem = asyncio.Semaphore(3) # number of threads. High chance of not working if higher than 3.
failed_cities = []
start = 0
end = exe_range[1] - exe_range[0]

async def get_hotel(city, country_code, browser):
    async with sem:

        city_s = city.replace(" ", "+")
        checkin_date = (datetime.date.today() + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        checkout_date = (datetime.date.today() + datetime.timedelta(days=61)).strftime("%Y-%m-%d")
        hotel_list = []
        page = await browser.new_page()
        page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city_s}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=2&no_rooms=1&group_children=0&sb_travel_purpose=leisure'
    

        for _ in range(max_retries):
            try:
                await page.goto(page_url, timeout=60000)
                break
            except:
                print(f"Timeout error at {city}, retrying...")
        else:
            print(f"Failed to get hotel page at {city} after {max_retries} retries.")
            await page.close()
            failed_cities.append((city, country_code)) # Add the failed city to the list
            return [{'city' : city, "hotel": "Error: Hotel Not Found"}]
        
        hotels = await page.locator('//div[@data-testid="property-card"]').all()
        for count, hotel in enumerate(hotels):
            if (count == hotels_per_city):
                break
            hotel_dict = {'city': city}
            try:
                hotel_dict['hotel'] = await hotel.locator('//div[@data-testid="title"]').inner_text()
            except:
                print(f"get hotel name failed at {city}.")
                hotel_dict['hotel'] = 'Not Available'
            try:
                hotel_dict['price'] = await hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
            except:
                hotel_dict['price'] = 'Not Available'
            if(get_score_and_reviews):
                try:
                    hotel_dict['score'] = await hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
                except:
                    try:
                        hotel_dict['score'] = await hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
                    except:
                        hotel_dict['score'] = 'Not Available'
                try:
                    hotel_dict['reviews count'] = (await hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text()).split()[0]
                except:
                    hotel_dict['reviews count'] = 'Not Available'
            hotel_string = hotel_dict['hotel'].translate(str.maketrans("", "", string.punctuation)).replace("  "," ").replace(" ", "-")
            hotel_dict['url'] = f'https://www.booking.com/hotel/{country_code}/{hotel_string}'
            hotel_list.append(hotel_dict)
        await page.close()
        return hotel_list

async def main():
    global exe_list
    global end
    hotel_list = []
    city_counter = 0
    if os.path.exists(filename):
        hotel_df = pd.read_csv(filename)
        hotel_list = hotel_df.to_dict('records')
        exe_list['city'] = exe_list['city'] + ',' + exe_list['country'].replace(" ", "+")
        mask = exe_list['city'].isin(hotel_df['city'].unique())
        exe_list = exe_list[~mask]
        num_exed = len(hotel_df['city'].unique())
        end = end - num_exed
        print(f"Resuming from saved state with {num_exed} cities already scraped.")
    if (end <= 0 | end > exe_list.shape[0]):
        print("invalid range. Quiting.")
        return
    print(f"\nHotel scraping is starting. {end - start} cities will be searched.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        tasks = [get_hotel((exe_list.iat[i, 0]+','+exe_list.iat[i, 1]).replace(" ","+"), exe_list.iat[i, 2].lower(), browser) for i in range(start,end)]
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Scraping hotels. Do not quit or pause the script'):
            result = await future
            hotel_list.extend(result)
            city_counter += 1  # Increment the counter
            if city_counter % check_point_interval == 0:
                pd.DataFrame(hotel_list).to_csv(filename, index=False)
        await browser.close()
        if failed_cities:
            print(f"Rerunning the scraping for {len(failed_cities)} failed cities...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                tasks = [get_hotel(city, country_code, browser) for city, country_code in failed_cities]
                print(tasks)
                for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Scraping hotels'):
                    result = await future
                    hotel_list.extend(result)
                await browser.close()
    await pd.DataFrame(hotel_list).to_csv(filename)
    print("Done!")

# Run the main function
asyncio.run(main())