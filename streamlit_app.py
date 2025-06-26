import streamlit as st
import pandas as pd
import requests

API_URL = "https://stock-signal-35232a1d0473.herokuapp.com/signals/"

# 🧾 조건 설명표
conditions = {
    "S_MA_buy": "MA 조건",
    "S_MACD_buy": "MACD 조건",
    "S_RSI_buy": "RSI 조건",
    "S_BB_buy": "BollingerBand 조건",
    "S_DC_buy": "Donchian 고점 돌파",
    "S_Vol_buy": "거래량 급등",
    "S_RSI_sell": "RSI 조건",
    "S_BB_sell": "BollingerBand 조건",
    "S_DC_sell": "Donchian 저점 이탈",
    "S_Vol_sell": "거래량 급등"
}

st.title("📈 주식 시그널 검색기")
ticker = st.text_input("🔍 티커를 입력하세요 (예: AAPL, TSLA), 대소문자 구분 없음")

# 📋 조건 설명 표 출력
if ticker == "":
    st.subheader("📋 시그널 조건 설명")
    st.table(pd.DataFrame({
        "조건 이름": ["MA 조건", "MACD 조건", "RSI 조건", "BollingerBand 조건", "Donchian 고/저점", "거래량 급등"],
        "설명": [
            "50일 이평선이 200일 이평선을 상향 돌파",
            "MACD 히스토그램 > 0",
            "RSI < 30 (매수), > 70 (매도)",
            "종가가 밴드 아래 또는 위",
            "최근 20일 고점 돌파 / 저점 이탈",
            "20일 평균 대비 거래량 1.5배 초과"
        ]
    }))

if st.button("시그널 조회") and ticker:
    url = API_URL + ticker.upper()
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by="Date", ascending=False)

        # ✅ 상세 조건을 비고에 표시
        def explain(row):
            if row["Signal"] == 1:
                satisfied = [conditions[col] for col in conditions if col.startswith("S_") and "buy" in col and row.get(col, 0) == 1]
                return "매수: " + ", ".join(satisfied)
            elif row["Signal"] == -1:
                satisfied = [conditions[col] for col in conditions if col.startswith("S_") and "sell" in col and row.get(col, 0) == 1]
                return "매도: " + ", ".join(satisfied)
            else:
                return ""

        df["비고"] = df.apply(explain, axis=1)

        # ✅ 필요한 열만 보여주기
        columns_to_show = ["Date", "Signal", "Score_buy", "Score_sell", "비고"]
        st.dataframe(df[columns_to_show])
    else:
        st.error(f"❌ 오류: {response.json().get('detail', 'API 호출 실패')}")
