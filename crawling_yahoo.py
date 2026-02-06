import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import time

# Yahoo Finance는 봇 탐지를 까다롭게 하므로 헤더를 신경 써야 합니다.
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def load_existing_links(filename='yahoo_news.csv'):
    links = set()
    if os.path.isfile(filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) > 2:
                        links.add(row[2]) # Link index
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    return links

def get_article_content(url):
    try:
        time.sleep(1) # Polite delay
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return "Failed to retrieve content"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Yahoo News Content Selectors (These change frequently)
        # 1. caas-body (Common in Yahoo)
        content_div = soup.select_one('.caas-body')
        
        # 2. body-wrap
        if not content_div:
            content_div = soup.select_one('.body-wrap')
            
        # 3. Fallback: Find paragraph containers
        if content_div:
            return content_div.get_text(separator=' ', strip=True)
        else:
            # If no specific container found, try to grab p tags that look like article text
            ps = soup.find_all('p')
            text_content = []
            for p in ps:
                text = p.get_text().strip()
                if len(text) > 50: # Assume meaningful paragraph
                    text_content.append(text)
            
            if text_content:
                return ' '.join(text_content)
                
        return "Content extraction failed"
        
    except Exception as e:
        return f"Error: {e}"

def crawl_yahoo_finance():
    url = "https://finance.yahoo.com/topic/stock-market-news/"
    print(f"Crawling {url}...")
    
    existing_links = load_existing_links()
    new_data = []
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to access main page. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        
        print(f"Found {len(links)} links on page. Filtering...")
        
        processed_links = set() # To avoid duplicates in current run
        
        for a in links:
            title = a.get_text().strip()
            href = a.get('href', '')
            
            # Filter conditions
            if len(title) < 30: continue # Too short title
            if '/news/' not in href and 'finance.yahoo.com' not in href: continue
            
            # Normalize URL
            if not href.startswith('http'):
                full_link = f"https://finance.yahoo.com{href}"
            else:
                full_link = href
                
            # Deduplication
            if full_link in existing_links or full_link in processed_links:
                continue
                
            processed_links.add(full_link)
            
            print(f"Fetching: {title[:40]}...")
            content = get_article_content(full_link)
            
            new_data.append([
                get_current_time(),
                title,
                full_link,
                content
            ])
            
            if len(new_data) >= 10: # Limit to 10 articles per run for now
                break
                
    except Exception as e:
        print(f"Critical Error: {e}")
        
    # Save
    if new_data:
        file_exists = os.path.isfile('yahoo_news.csv')
        with open('yahoo_news.csv', 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Date', 'Title', 'Link', 'Content'])
            writer.writerows(new_data)
        print(f"\nSaved {len(new_data)} articles to yahoo_news.csv")
    else:
        print("\nNo new articles found.")

if __name__ == "__main__":
    crawl_yahoo_finance()