from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_loader import load_balance_csv, load_transactions_csv
from src.qa_engine import FinancialContext, answer_question

BASE_DIR = Path(__file__).parent
DEFAULT_BALANCE = BASE_DIR / "data" / "balance.csv"
DEFAULT_TRANSACTIONS = BASE_DIR / "data" / "transactions.csv"

st.set_page_config(
    page_title="금융 챗봇 MVP",
    page_icon="💬",
    layout="wide",
)

st.title("💬 금융 챗봇 MVP")
st.caption("잔고·매매내역 CSV를 읽고 질문에 답변합니다.")


@st.cache_data(show_spinner=False)
def load_data(balance_path: str, transactions_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    balance = load_balance_csv(balance_path)
    transactions = load_transactions_csv(transactions_path)
    return balance, transactions


def render_sidebar() -> tuple[Path, Path]:
    st.sidebar.header("데이터 설정")

    use_sample = st.sidebar.toggle("샘플 데이터 사용", value=True)

    if use_sample:
        balance_path = DEFAULT_BALANCE
        transactions_path = DEFAULT_TRANSACTIONS
        st.sidebar.info("기본 샘플 CSV를 사용 중입니다.")
    else:
        balance_file = st.sidebar.file_uploader("잔고 CSV", type=["csv"])
        transactions_file = st.sidebar.file_uploader("매매내역 CSV", type=["csv"])
        if not balance_file or not transactions_file:
            st.sidebar.warning("두 CSV 파일을 모두 업로드해 주세요.")
            st.stop()
        balance_path = Path(st.session_state.get("_balance_tmp", BASE_DIR / "data" / "_upload_balance.csv"))
        transactions_path = Path(
            st.session_state.get("_transactions_tmp", BASE_DIR / "data" / "_upload_transactions.csv")
        )
        balance_path.write_bytes(balance_file.getvalue())
        transactions_path.write_bytes(transactions_file.getvalue())

    st.sidebar.divider()
    st.sidebar.markdown("**잔고 CSV 컬럼**")
    st.sidebar.code("symbol, name, quantity, avg_price, current_price")
    st.sidebar.markdown("**매매내역 CSV 컬럼**")
    st.sidebar.code("date, type, symbol, name, quantity, price, amount")

    return balance_path, transactions_path


balance_path, transactions_path = render_sidebar()

try:
    balance_df, transactions_df = load_data(str(balance_path), str(transactions_path))
except Exception as exc:
    st.error(f"CSV 로드 실패: {exc}")
    st.stop()

ctx = FinancialContext(balance=balance_df, transactions=transactions_df)

tab_chat, tab_balance, tab_transactions = st.tabs(["챗봇", "잔고", "매매내역"])

with tab_chat:
    st.subheader("질문하기")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! 잔고와 매매내역에 대해 궁금한 점을 물어보세요.\n\n예: 총 평가금액 알려줘 / 보유 종목 보여줘 / 최근 매매내역",
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = answer_question(prompt, ctx)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

    st.divider()
    st.markdown("**빠른 질문**")
    cols = st.columns(4)
    quick_questions = [
        "총 평가금액 알려줘",
        "보유 종목 보여줘",
        "최근 매매내역 보여줘",
        "수익률 가장 좋은 종목은?",
    ]
    for col, q in zip(cols, quick_questions):
        if col.button(q, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})
            answer = answer_question(q, ctx)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

with tab_balance:
    st.subheader("잔고 현황")
    total_value = balance_df["market_value"].sum()
    total_pl = balance_df["profit_loss"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("총 평가금액", f"{total_value:,.0f}원")
    m2.metric("총 평가손익", f"{total_pl:,.0f}원")
    m3.metric("보유 종목", f"{len(balance_df)}개")

    display_balance = balance_df.copy()
    display_balance["return_pct"] = display_balance["return_pct"].map(lambda x: f"{x:+.2f}%")
    st.dataframe(
        display_balance[
            ["symbol", "name", "quantity", "avg_price", "current_price", "market_value", "profit_loss", "return_pct"]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tab_transactions:
    st.subheader("매매내역")
    display_tx = transactions_df.copy()
    display_tx["date"] = display_tx["date"].dt.strftime("%Y-%m-%d")
    display_tx["type"] = display_tx["type"].map({"buy": "매수", "sell": "매도"})
    st.dataframe(display_tx, use_container_width=True, hide_index=True)
