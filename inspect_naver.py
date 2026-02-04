import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_economy_news():
    print("\n[Naver Economy News - Finance Section]")
    url = "https://news.naver.com/breakingnews/section/101/259"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # New selector for the breaking news section
        headlines = soup.select('.sa_text_title')
        
        print(f"Found {len(headlines)} headlines.")
        
        for i, h in enumerate(headlines):
            text = h.get_text().strip()
            print(f"{i}: {text}")
                     
    except Exception as e:
        print(f"Error in Economy News: {e}")

def get_stock_news(page=1):
    print(f"\n[Naver Stock News - Page {page}]")
    url = f"https://finance.naver.com/news/mainnews.naver?&page={page}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Selectors for finance news
        headlines = soup.select('.mainNewsList li dl dd a')
        
        print(f"Found {len(headlines)} headlines.")
        for i, h in enumerate(headlines):
            text = h.get_text().strip()
            print(f"{i}: {text}")
            
    except Exception as e:
        print(f"Error in Stock News: {e}")

if __name__ == "__main__":
    get_economy_news()
    for page in range(1, 3):
        get_stock_news(page)