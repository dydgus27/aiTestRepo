# 금융 챗봇 MVP

Python + Streamlit 기반 금융 챗봇 MVP입니다. 잔고·매매내역 CSV를 읽고 사용자 질문에 답변합니다.

## 기능

- 잔고 CSV 읽기 및 평가금액·손익 계산
- 매매내역 CSV 읽기 및 정렬
- 자연어 질의응답 (규칙 기반)
- Streamlit 채팅 UI

## 프로젝트 구조

```
.
├── app.py                  # Streamlit 메인 앱
├── requirements.txt
├── data/
│   ├── balance.csv         # 샘플 잔고
│   └── transactions.csv    # 샘플 매매내역
└── src/
    ├── data_loader.py      # CSV 로더
    └── qa_engine.py        # Q&A 엔진
```

## CSV 형식

### 잔고 (`balance.csv`)

| 컬럼 | 설명 |
|------|------|
| symbol | 종목코드 |
| name | 종목명 |
| quantity | 보유 수량 |
| avg_price | 평균 매입가 |
| current_price | 현재가 |

### 매매내역 (`transactions.csv`)

| 컬럼 | 설명 |
|------|------|
| date | 거래일 (YYYY-MM-DD) |
| type | buy / sell |
| symbol | 종목코드 |
| name | 종목명 |
| quantity | 수량 |
| price | 단가 |
| amount | 거래금액 |

## 실행 방법

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

브라우저에서 `http://localhost:8501` 이 열립니다.

## 질문 예시

- 총 평가금액 알려줘
- 보유 종목 보여줘
- 삼성전자 보유량 알려줘
- 최근 매매내역 보여줘
- 매수 내역 요약해줘
- 월별 매매 요약
- 수익률 가장 좋은 종목은?

## 사이드바

- **샘플 데이터 사용**: 기본 제공 CSV 사용
- **파일 업로드**: 직접 CSV 업로드 후 분석
