# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import os

# File to store posted apprenticeship URLs
DATA_FILE = 'posted_apprenticeships.json'

def load_posted_apprenticeships():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return []

def save_posted_apprenticeships(posted):
    with open(DATA_FILE, 'w') as file:
        json.dump(posted, file)

def fetch_page(url, params):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f'Error fetching the webpage: {e}')
        return None

def find_new_apprenticeships_ukgov():
    APPRENTICESHIP_URL = 'https://www.findapprenticeship.service.gov.uk/apprenticeships?sort=AgeAsc&searchTerm=&location=&distance=all&levelIds=4&levelIds=5&levelIds=6&levelIds=7'
    PARAMS = {
    "sort": "AgeAsc",
    "searchTerm": "",
    "location": "",
    "distance": "all",
    "levelIds": [4, 5, 6, 7], 
    "pageNumber": 1  
    }
    
    max_pages = 3  
    current_page = 1
    
    new_listings = []
    posted_apprenticeships = load_posted_apprenticeships()
    while current_page <= max_pages:
        PARAMS["pageNumber"] = current_page
        """Scrape the UK Government Apprenticeship Finder site and return new listings."""
        html = fetch_page(APPRENTICESHIP_URL, PARAMS)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
       
        listings = soup.find_all('li', class_='das-search-results__list-item govuk-!-padding-top-6')

        for listing in listings:
            title_element = listing.find('a', class_='das-search-results__link')
            title = title_element.text.strip()    
            link = title_element['href']
            full_link = f"https://www.findapprenticeship.service.gov.uk{link}"

            if full_link not in posted_apprenticeships:
                company = listing.find('p',class_='govuk-body govuk-!-margin-bottom-0').text.strip()
                location = listing.find('p', class_='govuk-body das-!-color-dark-grey').text.strip()
                training = listing.find('p', class_='govuk-body govuk-!-margin-bottom-1').text.replace("Training course", "").strip()
                posted = listing.find('p', class_= 'govuk-body govuk-!-font-size-16 das-!-color-dark-grey').text.strip()
                expires = listing.find('p', class_= 'govuk-body govuk-!-margin-bottom-0 govuk-!-margin-top-1').text.strip()
                
                salary_element = next((p for p in listing.find_all('p', class_='govuk-body') if p.get('class') == ['govuk-body']), None)
                salary = salary_element.text.replace("Annual wage", "").strip()
                
                new_listings.append((title, company, location, training, salary, posted, expires, full_link))
                posted_apprenticeships.append(full_link)
        
        current_page += 1

    print(posted_apprenticeships)
    save_posted_apprenticeships(list(posted_apprenticeships))
    return new_listings

def find_new_apprenticeships():
    ukgov_listings = find_new_apprenticeships_ukgov()
    return ukgov_listings
