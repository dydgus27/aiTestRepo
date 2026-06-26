from __future__ import annotations

import pandas as pd

from src.qa_engine import FinancialContext, _portfolio_summary


def build_financial_context_text(ctx: FinancialContext) -> str:
    """Gemini 프롬프트에 넣을 잔고·매매내역 컨텍스트 문자열을 생성합니다."""
    balance = ctx.balance.copy()
    transactions = ctx.transactions.copy()

    if not transactions.empty and "date" in transactions.columns:
        transactions["date"] = pd.to_datetime(transactions["date"]).dt.strftime("%Y-%m-%d")

    balance_csv = balance.to_csv(index=False) if not balance.empty else "(없음)"
    transactions_csv = transactions.to_csv(index=False) if not transactions.empty else "(없음)"

    return (
        f"## 포트폴리오 요약\n{_portfolio_summary(ctx)}\n\n"
        f"## 잔고 CSV\n{balance_csv}\n"
        f"## 매매내역 CSV\n{transactions_csv}"
    )
