from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


@dataclass
class FinancialContext:
    balance: pd.DataFrame
    transactions: pd.DataFrame


def _format_krw(value: float) -> str:
    return f"{value:,.0f}원"


def _format_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def _find_stock_name(text: str, balance: pd.DataFrame, transactions: pd.DataFrame) -> str | None:
    for name in balance["name"].tolist():
        if name in text:
            return name
    for name in transactions["name"].dropna().unique().tolist():
        if name in text:
            return name
    return None


def _portfolio_summary(ctx: FinancialContext) -> str:
    total_value = ctx.balance["market_value"].sum()
    total_cost = ctx.balance["cost_basis"].sum()
    total_pl = total_value - total_cost
    total_return = (total_pl / total_cost * 100) if total_cost else 0.0

    lines = [
        f"총 평가금액: {_format_krw(total_value)}",
        f"총 매입금액: {_format_krw(total_cost)}",
        f"총 평가손익: {_format_krw(total_pl)} ({_format_pct(total_return)})",
        f"보유 종목 수: {len(ctx.balance)}개",
    ]
    return "\n".join(lines)


def _holdings_list(ctx: FinancialContext) -> str:
    if ctx.balance.empty:
        return "보유 종목이 없습니다."

    lines = ["현재 보유 종목:"]
    for _, row in ctx.balance.iterrows():
        lines.append(
            f"- {row['name']}({row['symbol']}): {int(row['quantity'])}주, "
            f"평가 {_format_krw(row['market_value'])}, "
            f"손익 {_format_krw(row['profit_loss'])} ({_format_pct(row['return_pct'])})"
        )
    return "\n".join(lines)


def _stock_detail(ctx: FinancialContext, stock_name: str) -> str:
    holding = ctx.balance[ctx.balance["name"] == stock_name]
    if holding.empty:
        return f"'{stock_name}' 종목은 현재 보유하고 있지 않습니다."

    row = holding.iloc[0]
    tx = ctx.transactions[ctx.transactions["name"] == stock_name]
    buy_count = len(tx[tx["type"] == "buy"])
    sell_count = len(tx[tx["type"] == "sell"])

    return (
        f"{stock_name}({row['symbol']}) 보유 현황\n"
        f"- 보유 수량: {int(row['quantity'])}주\n"
        f"- 평균 매입가: {_format_krw(row['avg_price'])}\n"
        f"- 현재가: {_format_krw(row['current_price'])}\n"
        f"- 평가금액: {_format_krw(row['market_value'])}\n"
        f"- 평가손익: {_format_krw(row['profit_loss'])} ({_format_pct(row['return_pct'])})\n"
        f"- 누적 매매: 매수 {buy_count}건, 매도 {sell_count}건"
    )


def _recent_transactions(ctx: FinancialContext, limit: int = 5) -> str:
    if ctx.transactions.empty:
        return "매매내역이 없습니다."

    lines = [f"최근 매매내역 {min(limit, len(ctx.transactions))}건:"]
    for _, row in ctx.transactions.head(limit).iterrows():
        action = "매수" if row["type"] == "buy" else "매도"
        date_str = row["date"].strftime("%Y-%m-%d")
        lines.append(
            f"- {date_str} {action} {row['name']} {int(row['quantity'])}주 "
            f"@ {_format_krw(row['price'])} (금액 {_format_krw(row['amount'])})"
        )
    return "\n".join(lines)


def _transaction_summary(ctx: FinancialContext, tx_type: str | None = None) -> str:
    tx = ctx.transactions.copy()
    if tx_type:
        tx = tx[tx["type"] == tx_type]

    if tx.empty:
        label = "매매" if tx_type is None else ("매수" if tx_type == "buy" else "매도")
        return f"{label} 내역이 없습니다."

    total_amount = tx["amount"].sum()
    total_qty = tx["quantity"].sum()
    label = "전체 매매" if tx_type is None else ("매수" if tx_type == "buy" else "매도")
    return (
        f"{label} 요약\n"
        f"- 건수: {len(tx)}건\n"
        f"- 총 수량: {int(total_qty)}주\n"
        f"- 총 금액: {_format_krw(total_amount)}"
    )


def _monthly_summary(ctx: FinancialContext) -> str:
    tx = ctx.transactions.copy()
    if tx.empty:
        return "매매내역이 없습니다."

    tx["month"] = tx["date"].dt.to_period("M").astype(str)
    grouped = (
        tx.groupby(["month", "type"], as_index=False)["amount"]
        .sum()
        .sort_values("month", ascending=False)
    )

    lines = ["월별 매매 요약:"]
    for month in grouped["month"].unique():
        month_rows = grouped[grouped["month"] == month]
        buy = month_rows[month_rows["type"] == "buy"]["amount"].sum()
        sell = month_rows[month_rows["type"] == "sell"]["amount"].sum()
        lines.append(f"- {month}: 매수 {_format_krw(buy)}, 매도 {_format_krw(sell)}")
    return "\n".join(lines)


def _top_performer(ctx: FinancialContext, best: bool = True) -> str:
    if ctx.balance.empty:
        return "보유 종목이 없습니다."

    sorted_df = ctx.balance.sort_values("return_pct", ascending=not best)
    row = sorted_df.iloc[0]
    label = "수익률 최고" if best else "수익률 최저"
    return (
        f"{label} 종목: {row['name']}({row['symbol']})\n"
        f"- 수익률: {_format_pct(row['return_pct'])}\n"
        f"- 평가손익: {_format_krw(row['profit_loss'])}"
    )


def _help_message() -> str:
    return (
        "다음과 같은 질문을 할 수 있습니다:\n"
        "- 총 잔고 / 평가금액 알려줘\n"
        "- 보유 종목 보여줘\n"
        "- 삼성전자 보유량 알려줘\n"
        "- 최근 매매내역 보여줘\n"
        "- 매수 내역 요약해줘\n"
        "- 월별 매매 요약\n"
        "- 수익률 가장 좋은 종목은?"
    )


def answer_question(question: str, ctx: FinancialContext) -> str:
    """규칙 기반 Q&A — CSV 데이터를 바탕으로 질문에 답합니다."""
    text = question.strip()
    if not text:
        return "질문을 입력해 주세요."

    stock_name = _find_stock_name(text, ctx.balance, ctx.transactions)

    if any(k in text for k in ("도움", "help", "무엇", "뭐", "질문")) and "?" in text:
        return _help_message()

    if stock_name and any(k in text for k in ("보유", "수량", "얼마", "현황", "잔고")):
        return _stock_detail(ctx, stock_name)

    if any(k in text for k in ("보유 종목", "종목 목록", "포트폴리오", "보유목록")):
        return _holdings_list(ctx)

    if any(k in text for k in ("최근", "매매내역", "거래내역", "체결")):
        limit = 10 if "10" in text else 5
        return _recent_transactions(ctx, limit=limit)

    if "매수" in text and any(k in text for k in ("요약", "내역", "얼마", "총")):
        return _transaction_summary(ctx, tx_type="buy")

    if "매도" in text and any(k in text for k in ("요약", "내역", "얼마", "총")):
        return _transaction_summary(ctx, tx_type="sell")

    if any(k in text for k in ("월별", "월간")):
        return _monthly_summary(ctx)

    if any(k in text for k in ("최고", "베스트", "1등", "가장 좋")) and "수익" in text:
        return _top_performer(ctx, best=True)

    if any(k in text for k in ("최저", "워스트", "가장 나쁜", "가장 안 좋")) and "수익" in text:
        return _top_performer(ctx, best=False)

    if any(k in text for k in ("총", "전체", "평가금액", "잔고", "자산")):
        return _portfolio_summary(ctx)

    if re.search(r"(매매|거래).*(요약|통계)", text):
        return _transaction_summary(ctx)

    if stock_name:
        return _stock_detail(ctx, stock_name)

    return (
        "질문을 이해하지 못했습니다. 아래 예시를 참고해 주세요.\n\n"
        + _help_message()
    )
