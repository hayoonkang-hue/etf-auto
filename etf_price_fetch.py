"""
보유 ETF 현재가 조회 스크립트
- 국내 ETF: pykrx 사용
- 해외 ETF (참고용): yfinance 사용

설치:
    pip install pykrx yfinance pandas
실행:
    python etf_price_fetch.py
"""

from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# ── 보유 ETF 목록 (이름 → 종목코드) ──────────────────────────────────────
# 국내 상장 ETF (KRX)
DOMESTIC_ETF = {
    "TIGER 반도체TOP10커버드콜액티브":      "469070",
    "KODEX 금융고배당TOP10타겟위클리커버드콜": "480040",
    "TIGER 배당커버드콜액티브":             "468380",
    "KODEX 200타겟위클리커버드콜":          "447770",
    "PLUS 금채권혼합":                     "458730",
    "PLUS 고배당주":                       "266160",
    "KODEX 머니마켓액티브":                "461250",
    "SOL 코리아고배당":                    "441640",
    "PLUS 자사주매입고배당주":             "494790",
    "KODEX 미국배당커버드콜액티브":        "487160",
    "TIGER 미국나스닥100타겟데일리커버드콜": "474220",
    "RISE 미국AI밸류체인데일리고정커버드콜": "480460",
    "ACE 미국나스닥100":                   "367380",
    "TIGER 미국초단기(3개월이하)국채":      "438330",
    "TIGER 미국S&P500선물(H)":             "143850",
    "TIGER 미국필라델피아반도체나스닥":     "381170",
    "KODEX 미국배당다우존스":              "446720",
    "KODEX 미국S&P500":                   "379800",
}

def get_today_or_last_trading():
    """오늘 날짜 또는 가장 최근 거래일 반환 (YYYYMMDD)"""
    today = datetime.today()
    # 주말이면 금요일로 되돌림
    if today.weekday() == 5:   # 토요일
        today -= timedelta(days=1)
    elif today.weekday() == 6: # 일요일
        today -= timedelta(days=2)
    return today.strftime("%Y%m%d")

def fetch_domestic_prices():
    date = get_today_or_last_trading()
    print(f"\n📅 조회 기준일: {date}\n")
    print(f"{'ETF 이름':<45} {'종목코드':<10} {'현재가(원)':>12} {'전일대비':>10} {'등락률':>8}")
    print("─" * 90)

    results = []
    for name, code in DOMESTIC_ETF.items():
        try:
            # 당일 OHLCV 조회 (당일 데이터 없으면 최근 5일치에서 마지막 행 사용)
            df = stock.get_market_ohlcv(date, date, code)
            if df.empty:
                # 최근 5거래일로 재시도
                start = (datetime.strptime(date, "%Y%m%d") - timedelta(days=7)).strftime("%Y%m%d")
                df = stock.get_market_ohlcv(start, date, code)
            if df.empty:
                raise ValueError("데이터 없음")

            row = df.iloc[-1]
            close   = int(row["종가"])
            change  = int(row["등락"])      if "등락" in df.columns else 0
            pct     = float(row["등락률"])   if "등락률" in df.columns else 0.0
            sign    = "▲" if change > 0 else ("▼" if change < 0 else "-")
            results.append({
                "ETF": name, "코드": code,
                "현재가": close, "전일대비": change, "등락률": pct
            })
            print(f"{name:<45} {code:<10} {close:>12,}  {sign}{abs(change):>8,}  {pct:>+7.2f}%")
        except Exception as e:
            results.append({"ETF": name, "코드": code, "현재가": "조회실패", "전일대비": "-", "등락률": "-"})
            print(f"{name:<45} {code:<10} {'조회실패':>12}  (사유: {e})")

    return pd.DataFrame(results)

if __name__ == "__main__":
    print("=" * 90)
    print("  보유 ETF 현재가 조회  (pykrx 기반)")
    print("=" * 90)

    df = fetch_domestic_prices()

    # CSV 저장
    out_file = f"etf_prices_{datetime.today().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"\n✅ 결과가 {out_file} 에 저장되었습니다.")
