import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import sys
import traceback
import subprocess
def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-css")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.cookies": 2,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    })
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def handle_cookie_banner(driver):
    try:
        cookie_banner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cookie-law-info-bar"))
        )
        accept_button = cookie_banner.find_element(By.ID, "cookie_action_close_header")
        driver.execute_script("arguments[0].click();", accept_button)
        print("Cookie banner accepted")
        # Wait for the banner to disappear
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "cookie-law-info-bar"))
        )
    except (TimeoutException, NoSuchElementException):
        print("No cookie banner found or unable to interact with it")

def scroll_and_load_comments(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    try:
        handle_cookie_banner(driver)
        iframe = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='https://disqus.com/embed/comments/?base=default&f=ecw']"))
        )
        print("Found Disqus Iframe")
        
        driver.switch_to.frame(iframe)
        print("Switched to Disqus iframe successfully")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#posts"))
        )
        print("Comments section loaded")

        no_new_comments_count = 0
        previous_height = driver.execute_script("return document.body.scrollHeight")
        max_attempts = 3  # Maximum attempts without height change

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            
            try:
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-refresh__button"))
                )
                if load_more_button.is_displayed():
                    driver.execute_script("arguments[0].click();", load_more_button)
                    print("Clicked 'Load more comments' button")
                    time.sleep(2)
                    
                    # Check if new comments were loaded
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == previous_height:
                        no_new_comments_count += 1
                        if no_new_comments_count >= max_attempts:
                            print("No new comments loaded after multiple attempts. Breaking loop.")
                            break
                    else:
                        no_new_comments_count = 0
                        previous_height = new_height
                else:
                    print("'Load more comments' button not displayed")
                    break
            except (TimeoutException, ElementClickInterceptedException):
                print("No more 'Load more comments' button found or not clickable")
                break

        print("All comments loaded successfully.")
        
        iframe_content = driver.page_source
        driver.switch_to.default_content()
        print("Switched back to main content")
        
        return iframe_content
    except TimeoutException:
        print("Timed out waiting for comments to load. Proceeding without comments.")
        return None
     
def save_html(url, driver, output_dir):
    print(f"Processing: {url}")
    driver.get(url)
    
    # Scroll and load all comments, and get iframe content
    iframe_content = scroll_and_load_comments(driver)
    
    # Get the full HTML of the main page
    main_html = driver.page_source
    
    # Insert the iframe content into the main HTML
    if iframe_content:
        print("Inserting Disqus iframe content into the main HTML")
        main_html = main_html.replace('<div id="disqus_thread">', 
                                      f'<div id="disqus_thread">{iframe_content}')
    
    # Create a filename from the URL
    filename = url.split("/")[-2] + ".html"
    filepath = os.path.join(output_dir, filename)
    
    # Save the combined HTML
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(main_html)
    
    print(f"Saved: {filepath}")

def process_links_from_csv(csv_file, output_dir):
    driver = setup_driver()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row['url']
                filename = url.split("/")[-2] + ".html"
                filepath = os.path.join(output_dir, filename)
                
                if os.path.exists(filepath):
                    print(f"Skipping {url} - already scraped")
                    continue
                    
                save_html(url, driver, output_dir)
    finally:
        driver.quit()

def main():
    csv_file = "ecatworld_posts.csv"
    output_dir = "saved_html_pages"

    while True:
        try:
            process_links_from_csv(csv_file, output_dir)
            break
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"\nRetrying... ")
            
            print("Restarting script...\n")
            python = sys.executable
            subprocess.call([python] + sys.argv)


if __name__ == "__main__":
    main()