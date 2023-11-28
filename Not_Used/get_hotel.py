from playwright.sync_api import sync_playwright
import datetime
import pandas as pd

def get_hotel(city):
    
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

get_hotel("San Diego")