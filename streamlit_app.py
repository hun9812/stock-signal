# streamlit_app.py

import streamlit as st
import pandas as pd
import requests

API_URL = "https://stock-signal-35232a1d0473.herokuapp.com/signals/"

st.title("📈 주식 시그널 검색기")
ticker = st.text_input("🔍 티커를 입력하세요 (예: AAPL, TSLA), 대소문자 구분 없음")

if st.button("시그널 조회") and ticker:
    url = API_URL + ticker.upper()
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by="Date", ascending=False)
        st.dataframe(df)
    else:
        st.error(f"❌ 오류: {response.json().get('detail', 'API 호출 실패')}")
