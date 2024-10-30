import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

def scrape_ecatworld():
    url = "https://e-catworld.com/display-posts/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    for item in soup.find_all('li', class_='listing-item'):
        title = item.find('a', class_='title')
        date_span = item.find('span', class_='date')
        
        if title and date_span:
            post_url = title['href']
            post_title = title.text
            post_date = date_span.text.strip('()')
            
            # Convert date string to datetime object
            date_obj = datetime.strptime(post_date, '%m/%d/%Y')
            
            posts.append({
                'title': post_title,
                'url': post_url,
                'date': date_obj
            })
    
    return posts

def save_to_csv(posts, filename='ecatworld_posts.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'url', 'date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for post in posts:
            writer.writerow({
                'title': post['title'],
                'url': post['url'],
                'date': post['date'].strftime('%Y-%m-%d')
            })

if __name__ == "__main__":
    scraped_posts = scrape_ecatworld()
    save_to_csv(scraped_posts)
    print(f"Scraped {len(scraped_posts)} posts and saved to ecatworld_posts.csv")