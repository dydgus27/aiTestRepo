from __future__ import annotations

import google.generativeai as genai

from src.context_builder import build_financial_context_text
from src.qa_engine import FinancialContext

DEFAULT_MODEL = "gemini-3.1-flash-lite"

SYSTEM_INSTRUCTION = """당신은 금융 포트폴리오 분석 챗봇입니다.

규칙:
- 아래 제공된 잔고·매매내역 CSV 데이터만 근거로 답변하세요.
- 데이터에 없는 숫자, 종목, 거래는 만들지 마세요.
- 금액은 원(KRW) 단위로 쉼표를 넣어 표기하세요 (예: 1,234,000원).
- 답변은 한국어로 간결하고 친절하게 작성하세요.
- 계산이 필요하면 제공된 데이터를 바탕으로 정확히 계산하세요.

{context}
"""


def _to_gemini_history(messages: list[dict[str, str]]) -> list[dict]:
    """Streamlit 메시지 목록을 Gemini chat history 형식으로 변환합니다."""
    history: list[dict] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role == "user":
            history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            history.append({"role": "model", "parts": [content]})

    while history and history[0]["role"] != "user":
        history.pop(0)
    return history


def ask_gemini(
    question: str,
    ctx: FinancialContext,
    api_key: str,
    chat_history: list[dict[str, str]] | None = None,
    model_name: str = DEFAULT_MODEL,
) -> str:
    """Google AI Studio(Gemini) API로 질문에 답합니다."""
    if not api_key.strip():
        raise ValueError("Google AI Studio API 키가 필요합니다.")

    context_text = build_financial_context_text(ctx)
    genai.configure(api_key=api_key.strip())

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_INSTRUCTION.format(context=context_text),
    )

    history = _to_gemini_history(chat_history or [])
    chat = model.start_chat(history=history)

    response = chat.send_message(question)
    return response.text.strip()
