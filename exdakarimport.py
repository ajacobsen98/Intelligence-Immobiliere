import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import locale
import csv
import time

# Set locale to French for date parsing
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.utf8')
except locale.Error:
    print("French locale not available. Dates might not parse correctly.")

# Convert relative dates to absolute dates
def convert_to_absolute_date(date_str):
    today = datetime.now()
    if 'Hier' in date_str:
        return today - timedelta(days=1)
    elif 'aujourd\'hui' in date_str:
        return today
    weekdays = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    for i, day in enumerate(weekdays):
        if day in date_str:
            today_weekday = today.weekday()
            days_ago = (today_weekday - i) % 7
            days_ago = 7 if days_ago == 0 else days_ago
            return today - timedelta(days=days_ago)
    try:
        return datetime.strptime(date_str, "%d %b %Y")
    except ValueError:
        return date_str

# Filename for the CSV file
filename = "daily_listings.csv"

# Check if the CSV file exists and if not, create it and add the header
try:
    with open(filename, 'x', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Neighborhood', 'Square Meters', 'Number of Rooms', 'Listing Type', 'Price', 'Date of Listing'])
except FileExistsError:
    pass  # File already exists, no need to add the header

url = "https://www.expat-dakar.com/immobilier/dakar?sort=highest-price"
params = {'page': 1}

while True:
    print(f"Fetching page {params['page']}...")
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching page {params['page']}: Status code {response.status_code}")
        break
    
    soup = BeautifulSoup(response.content, 'html.parser')
    listings = soup.select('.listing-card--tab')
    
    if not listings:
        print("No listings found or end of listings.")
        break

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        for listing in listings:
            name = listing.find(class_='listing-card__header__title').get_text(strip=True)
            neighborhood = listing.find(class_='listing-card__header__location').get_text(strip=True).split(',')[0]
            square_meters_tag = listing.select_one('.listing-card__header__tags__item--square-metres')
            square_meters = square_meters_tag.get_text(strip=True) if square_meters_tag else 'N/A'
            number_of_rooms_tag = listing.select_one('.listing-card__header__tags__item--no-of-bedrooms')
            number_of_rooms = number_of_rooms_tag.get_text(strip=True) if number_of_rooms_tag else 'N/A'
            listing_type = listing['data-t-listing_category_slug'] if 'data-t-listing_category_slug' in listing.attrs else 'N/A'
            price = listing.select_one('.listing-card__price__value').get_text(strip=True).replace('\u202f', '')
            date_of_listing = convert_to_absolute_date(listing.find(class_='listing-card__header__date').get_text(strip=True))
            date_of_listing_str = date_of_listing.strftime("%Y-%m-%d") if isinstance(date_of_listing, datetime) else date_of_listing

            # Write data to CSV file
            writer.writerow([name, neighborhood, square_meters, number_of_rooms, listing_type, price, date_of_listing_str])
            print(f"Added to CSV: {name}")
    
    next_page = soup.select_one('a[rel="next"]')
    if not next_page:
        print("Reached the end of the listings.")
        break
    params['page'] += 1
    time.sleep(1)  # Rate limit handling
