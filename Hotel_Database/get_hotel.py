import asyncio
from playwright.async_api import async_playwright, Browser
from tqdm.asyncio import tqdm
import pandas as pd
import datetime, os
from unidecode import unidecode
'''
There are unsolved small bugs. (Duplicates occur when resuming from saved state.)
'''
# import database(s)
city_list_short = pd.read_csv("world_cities_major.csv", keep_default_na=False, encoding='utf_8')[['city','country','iso2']]

# configuration / parameters
exe_list = city_list_short
exe_range = (20000, 24000)
get_score_and_reviews = True
hotels_per_city = 5
max_retries = 5
filename = f"hotels{str(exe_range)}.csv"
check_point_interval = 20 # save file after this number of cities
timeout = 120000 # determined by the internet connection you have. If you keep getting timeout error, try a higher number.

sem = asyncio.Semaphore(3) # number of threads. High chance of not working if higher than 3.
failed_cities = []
start = 0
end = exe_range[1] - exe_range[0]
exe_list = exe_list.iloc[exe_range[0]:exe_range[1]]

async def get_hotel(city: str, browser: Browser):
    async with sem:

        city_s = city.replace(" ", "+")
        checkin_date = (datetime.date.today() + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        checkout_date = (datetime.date.today() + datetime.timedelta(days=61)).strftime("%Y-%m-%d")
        hotel_list = []
        page = await browser.new_page()
        page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city_s}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=2&no_rooms=1&group_children=0&sb_travel_purpose=leisure'
    

        for _ in range(max_retries):
            try:
                await page.goto(page_url, timeout=timeout)
                break
            except:
                print(f"\nTimeout error at {city}, retrying...")
        else:
            print(f"\nFailed to get hotel page at {city} after {max_retries} retries.")
            await page.close()
            failed_cities.append((city)) # Add the failed city to the list
            return [{'city' : city, "hotel": "Error: Page Not Found"}]
        
        hotels = await page.locator('//div[@data-testid="property-card"]').all()
        if (len(hotels) == 0):
            await page.close()
            return [{'city' : city, "hotel": "No Avaliable Hotel"}]
        for count, hotel in enumerate(hotels):
            if (count == hotels_per_city):
                break
            hotel_dict = {'city': city}
            try:
                hotel_dict['hotel'] = await hotel.locator('//div[@data-testid="title"]').inner_text()
            except:
                print(f"\nGet hotel name failed at {city}.")
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
            try:
                url = await hotel.locator('//a[@data-testid="title-link"]').get_attribute('href')
                hotel_dict['url'] = url.split('?')[0]
            except:
                hotel_dict['url'] = f'https://www.booking.com/searchresults.en-us.html?ss={hotel_dict["hotel"].replace(" ","+")}'
            hotel_list.append(hotel_dict)
        await page.close()
        return hotel_list

async def main():
    global exe_list
    global end
    hotel_list = []
    city_counter = 0
    if os.path.exists(filename):
        hotel_df = pd.read_csv(filename).drop_duplicates(subset=['city','hotel'],keep='last',ignore_index=True)
        hotel_list = hotel_df.to_dict('records')
        temp = exe_list.copy()
        temp.loc[:, 'city_country'] = (exe_list['city']) + ',' + (exe_list['country'])
        mask = temp['city_country'].isin(hotel_df['city'].str.replace("+", " "))
        exe_list = exe_list[~mask]
        num_exed = len(hotel_df['city'].unique())
        end = end - num_exed
        print(f"\nResuming from saved state with {num_exed} cities already scraped.")
    if (end <= 0 or end > exe_list.shape[0]):
        print("\ninvalid range. Quiting.")
        return
    
    print(f"\n{end - start} cities will be scraped.\n")
    print("\n===============================================================================")
    print(f"   Do not modify the auto-generated webpages or hotel{str(exe_range)}.csv file.   ")
    print("===============================================================================\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        tasks = [get_hotel(unidecode(exe_list.iat[i, 0]+','+exe_list.iat[i, 1]).replace(" ","+"), browser) for i in range(start,end)]
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Scraping hotels. Press Ctrl + C to quit'):
            result = await future
            hotel_list.extend(result)
            city_counter += 1  # Increment the counter
            if city_counter % check_point_interval == 0:
                pd.DataFrame(hotel_list).to_csv(filename, index=False)
        await browser.close()
        if failed_cities:
            print(f"\nRerunning the scraping for {len(failed_cities)} failed cities...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                tasks = [get_hotel(city, browser) for city in failed_cities]
                for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Scraping hotels'):
                    result = await future
                    hotel_list.extend(result)
                await browser.close()
    pd.DataFrame(hotel_list).reset_index(drop=True).to_csv(filename, index=False)
    print("Done!")

# Run the main function
asyncio.run(main())