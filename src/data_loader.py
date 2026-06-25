from pathlib import Path

import pandas as pd

BALANCE_COLUMNS = ["symbol", "name", "quantity", "avg_price", "current_price"]
TRANSACTION_COLUMNS = ["date", "type", "symbol", "name", "quantity", "price", "amount"]


def _resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def load_balance_csv(path: str | Path) -> pd.DataFrame:
    """잔고 CSV를 읽고 평가금액·손익 컬럼을 계산합니다."""
    df = pd.read_csv(_resolve_path(path))
    missing = set(BALANCE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"잔고 CSV에 필수 컬럼이 없습니다: {', '.join(sorted(missing))}")

    df = df[BALANCE_COLUMNS].copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["avg_price"] = pd.to_numeric(df["avg_price"], errors="coerce")
    df["current_price"] = pd.to_numeric(df["current_price"], errors="coerce")
    df["market_value"] = df["quantity"] * df["current_price"]
    df["cost_basis"] = df["quantity"] * df["avg_price"]
    df["profit_loss"] = df["market_value"] - df["cost_basis"]
    df["return_pct"] = (df["profit_loss"] / df["cost_basis"] * 100).where(df["cost_basis"] > 0)
    return df


def load_transactions_csv(path: str | Path) -> pd.DataFrame:
    """매매내역 CSV를 읽고 날짜·금액을 정규화합니다."""
    df = pd.read_csv(_resolve_path(path))
    missing = set(TRANSACTION_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"매매내역 CSV에 필수 컬럼이 없습니다: {', '.join(sorted(missing))}")

    df = df[TRANSACTION_COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["type"] = df["type"].str.strip().str.lower()
    return df.sort_values("date", ascending=False).reset_index(drop=True)
