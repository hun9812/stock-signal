import streamlit as st
import pandas as pd
import requests

API_URL = "https://stock-signal-35232a1d0473.herokuapp.com/signals/"

st.set_page_config(page_title="주식 시그널 검색기", layout="wide")

st.title("\U0001F4C8 주식 시그널 검색기")

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
with st.container():
    st.subheader("\U0001F9FE 시그널 조건 설명")
    st.dataframe(cond_df, use_container_width=True, height=300)

# 입력
st.subheader("\U0001F50D 티커 검색")
ticker = st.text_input("티커를 입력하세요 (예: AAPL, TSLA)", value="")
query = st.button("시그널 조회")

# 데이터 처리 분리
def fetch_signals(ticker):
    url = API_URL + ticker.upper()
    response = requests.get(url)
    if response.status_code != 200:
        return None, response.json().get("detail", "API 호출 실패")
    data = response.json()
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date", ascending=True).reset_index(drop=True)

    # 각각 만족한 조건 리스트 추가
    def get_satisfied_conditions(row, mode):
        return [conditions[k] for k in conditions if mode in k and row.get(k) == 1]

    df["만족한 매수 조건"] = df.apply(lambda row: ", ".join(get_satisfied_conditions(row, "buy")), axis=1)
    df["만족한 매도 조건"] = df.apply(lambda row: ", ".join(get_satisfied_conditions(row, "sell")), axis=1)
    df["Score_buy"] = df["Score_buy"].astype(int)
    df["Score_sell"] = df["Score_sell"].astype(int)

    return df, None

# 조회 결과 출력
if query and ticker:
    df, error = fetch_signals(ticker)
    if error:
        st.error(f"❌ 오류: {error}")
    else:
        st.subheader("\U0001F4CA 시그널 결과")
        display_cols = [
            "Date",
            "Signal",
            "Score_buy",
            "Score_sell",
            "만족한 매수 조건",
            "만족한 매도 조건"
        ]
        st.dataframe(df[display_cols], use_container_width=True)
