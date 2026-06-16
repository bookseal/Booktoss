"""BookToss v0.0.1 — Streamlit "Hello, BookToss".

목표: 브라우저에 첫 화면이 뜬다. 로직 없음 — 이후 단계의 결과를 볼 자리를 먼저 만든다.
실행: streamlit run app.py  →  http://localhost:8501
"""
import streamlit as st

st.set_page_config(page_title="BookToss", page_icon="📚", layout="centered")
st.title("📚 BookToss")
st.caption("서울 도서관을 한 번에 검색하는 AI 에이전트 · v0.0.1")

st.write("서울 곳곳의 도서관을 **한 번에** 검색하는 AI 에이전트입니다. 찾는 책을 입력해 보세요.")

# 이 입력칸과 버튼이 앞으로 v0.1.0의 진짜 검색창으로 자랍니다.
book = st.text_input("찾는 책 제목", placeholder="예: 코스모스")
if st.button("검색", type="primary"):
    if book:
        st.info(f"'{book}' 검색은 다음 버전에서 연결됩니다. (지금은 화면만!)")
    else:
        st.warning("책 제목을 입력해 주세요.")
