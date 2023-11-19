from playwright.sync_api import sync_playwright
import datetime
import pandas as pd

def get_hotels(city):
    with sync_playwright() as p:

        city = city.replace(" ", "+")
        
        # IMPORTANT: dates must be future dates, otherwise it won't work
        checkin_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        checkout_date = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        hotels_list = []

        page_num = 1
        items_per_page = 0

        while (items_per_page >= 0):
            offset = str((page_num - 1) * items_per_page)
            page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure&offset={offset}'.replace("{checkin_date}",checkin_date).replace("{checkout_date}",checkout_date).replace("{city}", city).replace("{offset}", offset)

            page.goto(page_url, timeout=100000)

            hotels = page.locator('//div[@data-testid="property-card"]').all()
            print(f'There are {len(hotels)} hotels in page {page_num}.')
            items_per_page = len(hotels) - 1
            page_num += 1

            for hotel in hotels:
                hotel_dict = {}
                hotel_dict['hotel'] = hotel.locator('//div[@data-testid="title"]').inner_text()
                hotel_dict['price'] = hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
                #hotel_dict['score'] = hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
                #hotel_dict['avg review'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
                #hotel_dict['reviews count'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text().split()[0]

                hotels_list.append(hotel_dict)
        
        df = pd.DataFrame(hotels_list).drop_duplicates()
        print(df)
        
        browser.close()

get_hotels("San Diego")