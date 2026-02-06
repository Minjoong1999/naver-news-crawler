import os
import csv
import json
import requests
import google.generativeai as genai
from datetime import datetime

# 환경 변수에서 키 가져오기 (GitHub Secrets에 등록될 값들)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def load_news_data(filename, limit=20):
    """CSV에서 최신 뉴스 기사 로드"""
    articles = []
    if os.path.isfile(filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None) # Skip header
                # 리스트로 변환 후 뒤에서부터(최신) 슬라이싱
                rows = list(reader)
                
                # 날짜 컬럼 인덱스 찾기 (보통 0번)
                # 오늘 날짜 필터링을 하면 좋겠지만, 데이터가 적을 수 있으니 최근 N개로 진행
                recent_rows = rows[-limit:] if len(rows) > limit else rows
                
                for row in recent_rows:
                    if len(row) >= 3:
                        # Title, Content, Link 추출 (CSV 구조에 따라 인덱스 조정 필요)
                        # Naver: Date, Category, Title, Content, Link (Content=3)
                        # Yahoo: Date, Title, Link, Content (Content=3)
                        
                        title = row[2] if 'naver' in filename else row[1]
                        content = row[3] if len(row) > 3 else ""
                        
                        # 본문이 너무 길면 자름 (토큰 절약)
                        if len(content) > 500:
                            content = content[:500] + "..."
                        
                        # 안전한 문자열 포매팅
                        article_text = f"- 제목: {title}" + "\n" + f"- 내용: {content}"
                        articles.append(article_text)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    return articles

def analyze_trends(naver_news, yahoo_news):
    """Gemini API를 사용하여 시장 트렌드 분석"""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found. Skipping analysis.")
        return None

    genai.configure(api_key=GEMINI_API_KEY)
    
    # 무료 버전인 gemini-2.0-flash 또는 gemini-1.5-flash 사용 권장 (속도/가성비)
    # 모델명은 상황에 따라 변경 가능
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    너는 20년 경력의 베테랑 글로벌 펀드매니저이자 시장 분석가야.
    아래 제공된 한국(Naver)과 미국(Yahoo)의 최신 금융 뉴스들을 바탕으로, 
    오늘의 시장 트렌드 리포트를 작성해서 동료들에게 슬랙으로 브리핑해줘.

    [작성 가이드]
    1. **시장 분위기 (Sentiment):** 0~100점 (0:공포, 100:환호)으로 점수를 매기고 한 줄 평.
    2. **핵심 트렌드 3가지:** 오늘 가장 중요한 이슈 3가지를 요약.
    3. **주목할 섹터/종목:** 상승세거나 이슈가 있는 섹터 언급.
    4. **리스크 요인:** 주의해야 할 악재가 있다면 언급.
    5. **어조:** 전문적이지만 읽기 쉽게, 명확하게 (마크다운 형식 사용).

    ---
    [국내 뉴스 (Naver Finance)]
    {chr(10).join(naver_news)}

    [해외 뉴스 (Yahoo Finance)]
    {chr(10).join(yahoo_news)}
    ---
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"분석 실패: {e}"

def send_to_slack(message):
    """분석 결과를 슬랙으로 전송"""
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not found. Skipping Slack notification.")
        print("--- Analysis Result (Local View) ---")
        print(message)
        return

    payload = {
        "text": "📊 *오늘의 증시 트렌드 리포트* (by Gemini)",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 Date: {datetime.now().strftime('%Y-%m-%d')} | Powered by Gemini API"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Slack notification sent successfully.")
    except Exception as e:
        print(f"Error sending to Slack: {e}")

if __name__ == "__main__":
    print("Loading news data...")
    # 최근 15개씩 로드
    naver_news = load_news_data('news_data.csv', limit=15)
    yahoo_news = load_news_data('yahoo_news.csv', limit=15)
    
    if not naver_news and not yahoo_news:
        print("No news data found to analyze.")
        exit()
        
    print(f"Loaded {len(naver_news)} Naver articles and {len(yahoo_news)} Yahoo articles.")
    
    print("Analyzing with Gemini...")
    analysis_result = analyze_trends(naver_news, yahoo_news)
    
    if analysis_result:
        send_to_slack(analysis_result)