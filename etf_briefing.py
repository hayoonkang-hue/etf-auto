import datetime
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import yfinance as yf
from pykrx import stock
from googletrans import Translator # pip install googletrans==4.0.0-rc1

# 1. 포트폴리오 종목 및 티커 매핑
domestic_etfs = {
    "482730": "TIGER 반도체TOP10커버드콜액티브",
    "498410": "KODEX 금융고배당TOP10타겟위클리커버드콜",
    "472150": "TIGER 배당커버드콜액티브",
    "498400": "KODEX 200타겟위클리커버드콜",
    "0138Y0": "PLUS 금채권혼합",
    "161510": "PLUS 고배당주",
    "488770": "KODEX 머니마켓액티브",
    "0105E0": "SOL 코리아고배당",
    "0098N0": "PLUS 자사주매입고배당주"
}

overseas_etfs = {
    "441640": "KODEX 미국배당커버드콜액티브",
    "486290": "TIGER 미국나스닥100타겟데일리커버드콜",
    "490590": "RISE 미국AI밸류체인데일리고정커버드콜",
    "367380": "ACE 미국나스닥100",
    "0046A0": "TIGER 미국초단기(3개월이하)국채",
    "143850": "TIGER 미국S&P500선물(H)",
    "381180": "TIGER 미국필라델피아반도체나스닥",
    "489250": "KODEX 미국배당다우존스",
    "379800": "KODEX 미국S&P500"
}

translator = Translator()
today = datetime.datetime.now().strftime("%Y%m%d")
md_lines = [f"# 📊 ETF 일일 브리핑 ({datetime.datetime.now().strftime('%Y년 %m월 %d일')})\n"]
md_lines.append("## 📈 포트폴리오 가격 요약\n| 종목명 | 당일 가격 | 전일 대비 변동률 |\n|---|---|---|")

briefing_summary_data = []

# 2. 가격 정보 수집 (pykrx & yfinance)
def get_price_data():
    all_etfs = {**domestic_etfs, **overseas_etfs}
    for ticker, name in all_etfs.items():
        try:
            yf_ticker = yf.Ticker(f"{ticker}.KS")
            hist = yf_ticker.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                curr_price = hist['Close'].iloc[1]
                change_pct = ((curr_price - prev_close) / prev_close) * 100
                
                md_lines.append(f"| {name} | {curr_price:,.0f}원 | {change_pct:+.2f}% |")
                
                if change_pct >= 1.5 or change_pct <= -1.5:
                    briefing_summary_data.append(f"{name} {change_pct:+.1f}%")
            else:
                md_lines.append(f"| {name} | 데이터 없음 | - |")
        except Exception as e:
            md_lines.append(f"| {name} | 조회 오류 | - |")

# 3. 뉴스 수집 및 번역 (Google News RSS & yfinance)
def get_news_data():
    md_lines.append("\n## 📰 종목별 최신 뉴스 (Top 3)\n")
    
    for ticker, name in domestic_etfs.items():
        query = urllib.parse.quote(name)
        url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
        response = requests.get(url)
        root = ET.fromstring(response.text)
        
        md_lines.append(f"### 🇰🇷 {name}")
        items = root.findall('.//item')[:3]
        if items:
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                md_lines.append(f"- [{title}]({link})")
        else:
            md_lines.append("- 금일 관련 뉴스가 없습니다.")
            
    for ticker, name in overseas_etfs.items():
        yf_ticker = yf.Ticker(f"{ticker}.KS")
        news = yf_ticker.news
        md_lines.append(f"\n### 🌎 {name}")
        
        if news:
            for n in news[:3]:
                eng_title = n.get('title', '')
                link = n.get('link', '')
                try:
                    kor_title = translator.translate(eng_title, dest='ko').text
                except:
                    kor_title = eng_title
                md_lines.append(f"- [{kor_title}]({link})")
        else:
             md_lines.append("- 금일 관련 뉴스가 없습니다.")

# 4. 종합 및 파일 생성
get_price_data()
get_news_data()

md_lines.append("\n## 💡 오늘의 핵심 한 줄")
md_lines.append("글로벌 변동성과 배당 수익률을 동시에 고려하여 포트폴리오의 안정성을 유지 중입니다.")

md_lines.append("\n## 🎯 오늘의 액션")
md_lines.append("변동폭이 큰 기술주 기반 커버드콜의 프리미엄 수익을 확인하고, 리밸런싱 필요 여부를 점검하세요.")

# Markdown 파일 저장
with open(f"ETF_Daily_Briefing_{today}.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

# 5. 카카오톡 메모챗용 200자 압축 요약
kakaotalk_summary = (
    f"[ETF 일일 브리핑]\n"
    f"시장 변동성 체크 및 배당 점검의 날!\n\n"
    f"📈 주요변동: {', '.join(briefing_summary_data[:4]) if briefing_summary_data else '큰 변동 없음'}\n"
    f"💡 핵심: 글로벌 변동성 장세, 배당 수익 통한 방어력 유지\n"
    f"🎯 액션: 기술주 커버드콜 프리미엄 점검 및 비중 리밸런싱 검토\n"
)

print(kakaotalk_summary)
