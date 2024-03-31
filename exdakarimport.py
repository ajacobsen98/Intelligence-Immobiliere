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

def calculate_days_listed(date_of_listing_str):
    """Calculate how many days a listing has been posted.
    Args:
    - date_of_listing_str (str): The date the listing was posted, in "YYYY-MM-DD" format.
    Returns:
    - int: The number of days the listing has been posted.
    """
    try:
        date_of_listing = datetime.strptime(date_of_listing_str, "%Y-%m-%d")
        today = datetime.now()
        return (today - date_of_listing).days
    except ValueError:
        # Return a default value or handle the error as appropriate
        return 'Unknown'

def convert_to_absolute_date(date_str):
    today = datetime.now()
    if 'Hier' in date_str:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif 'aujourd\'hui' in date_str:
        return today.strftime("%Y-%m-%d")
    weekdays = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    for i, day in enumerate(weekdays):
        if day in date_str:
            today_weekday = today.weekday()
            days_ago = (today_weekday - i) % 7
            days_ago = 7 if days_ago == 0 else days_ago
            return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    try:
        return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        return 'Unknown'

filename = "daily_listings.csv"
existing_listings = {}

# Load existing listings
try:
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = (row['Name'], row['Price'])
            existing_listings[key] = row
except FileNotFoundError:
    print("File not found. It will be created.")

url = "https://www.expat-dakar.com/immobilier/dakar?sort=highest-price"
params = {'page': 1}

while True:
    response = requests.get(url, params=params)
    if response.status_code != 200:
        break

    soup = BeautifulSoup(response.content, 'html.parser')
    listings = soup.select('.listing-card--tab')

    if not listings:
        break

    for listing in listings:
        name_tag = listing.find(class_='listing-card__header__title')
        name = name_tag.get_text(strip=True) if name_tag else 'Unknown'
        
        price_tag = listing.select_one('.listing-card__price__value')
        price = price_tag.get_text(strip=True).replace('\u202f', '') if price_tag else 'N/A'
        
        neighborhood_tag = listing.find(class_='listing-card__header__location')
        neighborhood = neighborhood_tag.get_text(strip=True).split(',')[0] if neighborhood_tag else 'N/A'
        
        square_meters_tag = listing.select_one('.listing-card__header__tags__item--square-metres')
        square_meters = square_meters_tag.get_text(strip=True) if square_meters_tag else 'N/A'
        
        number_of_rooms_tag = listing.select_one('.listing-card__header__tags__item--no-of-bedrooms')
        number_of_rooms = number_of_rooms_tag.get_text(strip=True) if number_of_rooms_tag else 'N/A'
        
        listing_type = listing.get('data-t-listing_category_title', 'N/A')

        key = (name, price)

        date_of_listing_tag = listing.find(class_='listing-card__header__date')
        date_of_listing_str = convert_to_absolute_date(date_of_listing_tag.get_text(strip=True)) if date_of_listing_tag else datetime.today().strftime("%Y-%m-%d")

        if key in existing_listings:
            existing_listings[key]['Days Listed'] = calculate_days_listed(existing_listings[key]['Date of Listing'])
        else:
            days_listed = calculate_days_listed(date_of_listing_str)
            existing_listings[key] = {
                'Name': name,
                'Neighborhood': neighborhood,
                'Square Meters': square_meters,
                'Number of Rooms': number_of_rooms,
                'Listing Type': listing_type,
                'Price': price,
                'Date of Listing': date_of_listing_str,
                'Days Listed': days_listed,
            }

    next_page = soup.select_one('a[rel="next"]')
    if not next_page:
        break
    params['page'] += 1
    time.sleep(1)

# Update the CSV file
with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Name', 'Neighborhood', 'Square Meters', 'Number of Rooms', 'Listing Type', 'Price', 'Date of Listing', 'Days Listed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for listing in existing_listings.values():
        writer.writerow(listing)
