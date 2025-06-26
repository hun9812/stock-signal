import streamlit as st
import pandas as pd
import requests

API_URL = "https://stock-signal-35232a1d0473.herokuapp.com/signals/"

st.set_page_config(page_title="주식 시그널 검색기", layout="wide")

st.title("📈 주식 시그널 검색기")

# 조건 설명 테이블
conditions = {
    "S_MA_buy": "50일 이평 > 200일 이평",
    "S_MACD_buy": "MACD 히스토그램 양전환",
    "S_RSI_buy": "RSI < 30",
    "S_BB_buy": "Bollinger 하단 이탈",
    "S_DC_buy": "20일 고점 돌파",
    "S_Vol_buy": "거래량 급등 (20일 평균의 1.5배)",
    "S_RSI_sell": "RSI > 70",
    "S_BB_sell": "Bollinger 상단 돌파",
    "S_DC_sell": "20일 저점 하회",
    "S_Vol_sell": "거래량 급등 (20일 평균의 1.5배)"
}

cond_df = pd.DataFrame(list(conditions.items()), columns=["조건 코드", "설명"])

# 조건 설명은 항상 표시되도록
st.subheader("🧾 시그널 조건 설명")
st.dataframe(cond_df, use_container_width=True, height=300)

# 입력
st.subheader("🔍 티커 검색")
ticker = st.text_input("티커를 입력하세요 (예: AAPL, TSLA)", value="")

if st.button("시그널 조회") and ticker:
    url = API_URL + ticker.upper()
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date", ascending=True).reset_index(drop=True)

        # 비고 열 추가
        def explain(row):
            satisfied = []
            if row.get("Signal") == 1:
                satisfied = [conditions[k] for k in conditions if "buy" in k and row.get(k) == 1]
                return ", ".join(satisfied)
            elif row.get("Signal") == -1:
                satisfied = [conditions[k] for k in conditions if "sell" in k and row.get(k) == 1]
                return ", ".join(satisfied)
            return ""

        df["비고"] = df.apply(explain, axis=1)

        # 원하는 열만 출력 + 비고 오른쪽 정렬
        display_cols = ["Date", "Signal", "Score_buy", "Score_sell", "비고"]
        st.subheader("📊 시그널 결과")
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.error(f"❌ 오류: {response.json().get('detail', 'API 호출 실패')}")
