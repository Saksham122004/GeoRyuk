import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from bs4 import BeautifulSoup

def create_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Uncomment to run without a window
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Use Stealth to bypass bot detection
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    return driver

def scrape_google_maps(query, max_results=10):
    driver = create_driver()
    driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
    
    # Let the page load
    time.sleep(random.uniform(5, 7))

    results = []
    processed_links = set()

    # Step 1: Scroll the sidebar to load more results
    print("Loading listings...")
    sidebar = driver.find_element(By.XPATH, '//div[@role="feed"]')
    
    while len(processed_links) < max_results:
        # Scroll down
        sidebar.send_keys(Keys.PAGE_DOWN)
        time.sleep(2)
        
        # Collect links to click
        links = driver.find_elements(By.CLASS_NAME, "hfpxzc") # Main listing link class
        for link in links:
            url = link.get_attribute("href")
            if url not in processed_links:
                processed_links.add(url)
                if len(processed_links) >= max_results:
                    break
        
        # Check if we've reached the end
        if "You've reached the end of the list" in driver.page_source:
            break

    # Step 2: Iterate and extract data
    print(f"Found {len(processed_links)} links. Extracting details...")
    
    for url in processed_links:
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        try:
            # Field Extraction logic based on current Google Maps HTML structure
            name = soup.find("h1").text if soup.find("h1") else "N/A"
            
            # Using specific data-item-id attributes to find address and phone
            address = "N/A"
            address_btn = soup.find("button", {"data-item-id": "address"})
            if address_btn:
                address = address_btn.get_text(strip=True)

            phone = "N/A"
            phone_btn = soup.find("button", {"aria-label": lambda x: x and "Phone" in x})
            if phone_btn:
                phone = phone_btn.get_text(strip=True)

            website = "N/A"
            site_link = soup.find("a", {"data-item-id": "authority"})
            if site_link:
                website = site_link.get("href")

            rating = "N/A"
            rating_tag = soup.find("span", {"class": "ceNzR"}) # Common rating container
            if rating_tag:
                rating = rating_tag.get_text(strip=True)

            results.append({
                "Name": name,
                "Rating": rating,
                "Address": address,
                "Phone": phone,
                "Website": website
            })
            print(f"Extracted: {name}")

        except Exception as e:
            print(f"Error parsing {url}: {e}")

    driver.quit()
    return results

def save_data(data, filename="maps_data.csv"):
    if not data:
        print("No data found.")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Success! Data saved to {filename}")

if __name__ == "__main__":
    search_term = input("What are you searching for (e.g., Pizza in New York)? ")
    count = int(input("How many results do you want to scrape? "))
    
    data = scrape_google_maps(search_term, count)
    save_data(data)