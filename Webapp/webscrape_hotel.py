from playwright.sync_api import sync_playwright
import datetime, string
from unidecode import unidecode

get_score_and_reviews = True
hotels_per_city = 5
max_retries = 5
timeout = 120000 # determined by the internet connection you have. If you keep getting timeout error, try a higher number.

def search_hotel(city:str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        city_s = city.replace(" ", "+")
        checkin_date = (datetime.date.today() + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        checkout_date = (datetime.date.today() + datetime.timedelta(days=61)).strftime("%Y-%m-%d")
        hotel_list = []
        page = browser.new_page()
        page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city_s}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=2&no_rooms=1&group_children=0&sb_travel_purpose=leisure'
        print("scraping hotels at "+city)
        for _ in range(max_retries):
            try:
                page.goto(page_url, timeout=timeout)
                break
            except:
                print(f"\nTimeout error at {city}, retrying...")
        else:
            print(f"\nFailed to get hotel page at {city} after {max_retries} retries.")
            page.close()
            return [{'city' : city, "hotel": "Error: Page Not Found"}]
        
        hotels = page.locator('//div[@data-testid="property-card"]').all()
        if (len(hotels) == 0):
            page.close()
            return [{'city' : city, "hotel": "No Avaliable Hotel"}]
        for count, hotel in enumerate(hotels):
            if (count == hotels_per_city):
                break
            hotel_dict = {'city': city}
            try:
                hotel_dict['hotel'] = hotel.locator('//div[@data-testid="title"]').inner_text()
            except:
                print(f"\nGet hotel name failed at {city}.")
                hotel_dict['hotel'] = 'Not Available'
            try:
                hotel_dict['price'] = hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
            except:
                hotel_dict['price'] = 'Not Available'
            if(get_score_and_reviews):
                try:
                    hotel_dict['score'] = hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
                except:
                    try:
                        hotel_dict['score'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
                    except:
                        hotel_dict['score'] = 'Not Available'
                try:
                    hotel_dict['reviews count'] = (hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text()).split()[0]
                except:
                    hotel_dict['reviews count'] = 'Not Available'
            try:
                hotel_dict['url'] = hotel.locator('//a[@data-testid="title-link"]').get_attribute('href').split('?')[0]
            except:
                hotel_dict['url'] = f'https://www.booking.com/searchresults.en-us.html?ss={hotel_dict["hotel"]+"+"+city}'
            hotel_list.append(hotel_dict)
        browser.close()
    return hotel_list