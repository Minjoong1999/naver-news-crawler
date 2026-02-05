import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime, timedelta
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_korean_time():
    """Returns current time in KST (UTC+9)"""
    return (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')

def load_existing_links():
    """Load existing news links from the CSV file to prevent duplicates."""
    links = set()
    if os.path.isfile('news_data.csv'):
        try:
            with open('news_data.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) > 4:
                        links.add(row[4])  # Link is at index 4
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
    return links

def get_article_content(url):
    try:
        time.sleep(0.5) # Be polite
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try common content selectors
        content = soup.select_one('#dic_area')
        if not content:
            content = soup.select_one('#articeBody')
        if not content:
            content = soup.select_one('.news_end')
        if not content:
            # For Finance News specific structure
            content = soup.select_one('.articleCont') 
            
        if content:
            return content.get_text().strip()
        return "Content not found"
    except Exception as e:
        return f"Error fetching content: {e}"

def save_to_csv(data):
    file_exists = os.path.isfile('news_data.csv')
    
    with open('news_data.csv', 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Category', 'Title', 'Content', 'Link'])
        
        for row in data:
            writer.writerow(row)
    print(f"Saved {len(data)} items to news_data.csv")

def get_economy_news(existing_links):
    print("\n[Naver Economy News - Finance Section]")
    url = "https://news.naver.com/breakingnews/section/101/259"
    results = []
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = soup.select('.sa_text_title')
        print(f"Found {len(headlines)} headlines.")
        
        for h in headlines:
            title = h.get_text().strip()
            link = h['href']
            
            if link in existing_links:
                print(f"Skipping duplicate: {title[:20]}...")
                continue
                
            print(f"Fetching: {title[:20]}...")
            content = get_article_content(link)
            
            results.append([
                get_korean_time(),
                'Economy',
                title,
                content,
                link
            ])
            
    except Exception as e:
        print(f"Error in Economy News: {e}")
        
    return results

def get_stock_news(page=1, existing_links=set()):
    print(f"\n[Naver Stock News - Page {page}]")
    url = f"https://finance.naver.com/news/mainnews.naver?&page={page}"
    results = []
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = soup.select('.mainNewsList li dl dd a')
        print(f"Found {len(headlines)} headlines.")
        
        for h in headlines:
            title = h.get_text().strip()
            link = h['href']
            
            if not link.startswith('http'):
                link = f"https://finance.naver.com{link}"
            
            if link in existing_links:
                print(f"Skipping duplicate: {title[:20]}...")
                continue
                
            print(f"Fetching: {title[:20]}...")
            content = get_article_content(link)
            
            results.append([
                get_korean_time(),
                'Stock',
                title,
                content,
                link
            ])
            
    except Exception as e:
        print(f"Error in Stock News: {e}")
        
    return results

if __name__ == "__main__":
    existing_links = load_existing_links()
    print(f"Loaded {len(existing_links)} existing links.")
    
    all_data = []
    
    # 1. Economy News
    economy_data = get_economy_news(existing_links)
    all_data.extend(economy_data)
    
    # 2. Stock News (Page 1 to 5)
    for page in range(1, 6):
        stock_data = get_stock_news(page, existing_links)
        all_data.extend(stock_data)
        
    # 3. Save
    if all_data:
        save_to_csv(all_data)
    else:
        print("No new news found.")
