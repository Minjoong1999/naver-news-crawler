import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

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
            
        if content:
            return content.get_text().strip()
        return "Content not found"
    except Exception as e:
        return f"Error fetching content: {e}"

def save_to_csv(data):
    # File name with Date? Or just one big file? 
    # Let's use one big file 'news_data.csv' for easy appending.
    file_exists = os.path.isfile('news_data.csv')
    
    with open('news_data.csv', 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Category', 'Title', 'Content', 'Link'])
        
        for row in data:
            writer.writerow(row)
    print(f"Saved {len(data)} items to news_data.csv")

def get_economy_news():
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
            
            print(f"Fetching: {title[:20]}...")
            content = get_article_content(link)
            
            results.append([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Economy',
                title,
                content,
                link
            ])
            
    except Exception as e:
        print(f"Error in Economy News: {e}")
        
    return results

def get_stock_news(page=1):
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
            # Finance news links might be relative or absolute.
            # Usually they are absolute like 'https://finance.naver.com/...'
            # But sometimes they redirect. Let's check.
            if not link.startswith('http'):
                link = f"https://finance.naver.com{link}"
                
            print(f"Fetching: {title[:20]}...")
            content = get_article_content(link)
            
            results.append([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Stock',
                title,
                content,
                link
            ])
            
    except Exception as e:
        print(f"Error in Stock News: {e}")
        
    return results

if __name__ == "__main__":
    all_data = []
    
    # 1. Economy News
    economy_data = get_economy_news()
    all_data.extend(economy_data)
    
    # 2. Stock News (Page 1 & 2)
    for page in range(1, 3):
        stock_data = get_stock_news(page)
        all_data.extend(stock_data)
        
    # 3. Save
    if all_data:
        save_to_csv(all_data)
