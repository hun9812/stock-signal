# app/main.py

from fastapi import FastAPI, HTTPException
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# 5TLAVRY8GONFLIJB
API_KEY = "5TLAVRY8GONFLIJB"

app = FastAPI(title="AlphaVantage 기반 실시간 주식 시그널 API")

def fetch_history(ticker: str,
                  start: str = "2022-01-01",
                  end:   str = "2025-06-26") -> pd.DataFrame:
    """
    Alpha Vantage 데일리 조정 종가 데이터 다운로드
    """
    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY_ADJUSTED"
        f"&symbol={ticker.upper()}"
        f"&outputsize=full"
        f"&apikey={API_KEY}"
    )
    res = requests.get(url)
    data = res.json()
    if "Time Series (Daily)" not in data:
        raise HTTPException(404, "티커 데이터를 찾을 수 없습니다.")
    ts = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(ts, orient="index", dtype=float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    # 필요한 기간, 칼럼만 추출
    df = df.loc[start:end, ["1. open","2. high","3. low","4. close","6. volume"]]
    df.columns = ["Open","High","Low","Close","Volume"]
    df.dropna(inplace=True)
    return df

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # 이동평균
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    # MACD
    ema_fast = df["Close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]   = df["MACD"] - df["MACD_signal"]
    # RSI
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
    # Bollinger Bands
    bb = BollingerBands(df["Close"], window=20, window_dev=2)
    df["BB_low"]  = bb.bollinger_lband()
    df["BB_high"] = bb.bollinger_hband()
    # Donchian Channel
    df["DC_high"] = df["Close"].rolling(20).max()
    df["DC_low"]  = df["Close"].rolling(20).min()
    # 거래량 20일 평균
    df["Vol20"]   = df["Volume"].rolling(20).mean()
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = add_indicators(df)
    # 매수 플래그
    df["S_MA_buy"]   = ((df["MA50"] > df["MA200"]) &
                        (df["MA50"].shift(1) <= df["MA200"].shift(1))).astype(int)
    df["S_MACD_buy"] = (df["MACD_hist"] > 0).astype(int)
    df["S_RSI_buy"]  = (df["RSI"] < 30).astype(int)
    df["S_BB_buy"]   = (df["Close"] < df["BB_low"]).astype(int)
    df["S_DC_buy"]   = (df["Close"] > df["DC_high"].shift(1)).astype(int)
    df["S_Vol_buy"]  = (df["Volume"] > df["Vol20"] * 1.5).astype(int)
    # 매도 플래그
    df["S_RSI_sell"] = (df["RSI"] > 70).astype(int)
    df["S_BB_sell"]  = (df["Close"] > df["BB_high"]).astype(int)
    df["S_DC_sell"]  = (df["Close"] < df["DC_low"].shift(1)).astype(int)
    df["S_Vol_sell"] = (df["Volume"] > df["Vol20"] * 1.5).astype(int)
    # 점수 합산
    buy_cols  = ["S_MA_buy","S_MACD_buy","S_RSI_buy","S_BB_buy","S_DC_buy","S_Vol_buy"]
    sell_cols = ["S_RSI_sell","S_BB_sell","S_DC_sell","S_Vol_sell"]
    df["Score_buy"]  = df[buy_cols].sum(axis=1)
    df["Score_sell"] = df[sell_cols].sum(axis=1)
    # 최종 시그널(동일=0, 다르면 큰 쪽)
    df["Signal"] = (
        (df["Score_buy"]  > df["Score_sell"]).astype(int)
      - (df["Score_sell"] > df["Score_buy"]).astype(int)
    )
    return df

@app.get("/signals/{ticker}")
def get_signals(ticker: str):
    """
    HTTP GET /signals/{ticker}
    실시간으로 해당 종목 데이터를 받아와 지표·시그널을 계산한 후 JSON으로 반환합니다.
    """
    df = fetch_history(ticker)
    df = generate_signals(df)
    out = df.reset_index()[["Date","Signal","Score_buy","Score_sell"]]
    return out.to_dict(orient="records")
