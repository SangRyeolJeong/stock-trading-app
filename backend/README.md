# MOA API

FastAPI 기반의 MOA 백엔드입니다. 비동기 시세 스트림, 모의 주문, 포트폴리오,
절세 계산 및 전략 추천을 제공하는 것을 목표로 합니다.

현재는 한투 API 키 없이도 프론트엔드 개발과 테스트가 가능하도록
`MockMarketDataProvider`가 기본값입니다. 주문은 PostgreSQL 원장에 영속화되며,
단일 데모 사용자의 원화·달러 초기 잔액이 첫 조회 또는 주문 시 생성됩니다.

## 로컬 실행

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
pytest
uvicorn app.main:app --reload --port 8000
```

현재 작업 환경처럼 WSL의 `python3-venv`가 없는 경우 Windows PowerShell에서
Python 3.12 가상환경을 사용할 수 있습니다.

```powershell
cd D:\programming\backend
py -3.12 -m venv .venv-win
.\.venv-win\Scripts\python -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python -m alembic upgrade head
.\.venv-win\Scripts\python -m pytest
.\.venv-win\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

실행 후 확인:

- API 상태: `http://localhost:8000/health`
- API 문서: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

## 현재 구조

```text
app/
├── api/              # HTTP/WebSocket 라우터
├── core/             # 환경설정과 공통 예외
├── db/               # 비동기 SQLAlchemy 엔진과 세션
├── integrations/kis/ # 한국투자증권 경계
├── models/           # 모의 계좌, 주문, 체결, 원장과 포지션
├── schemas/          # 요청·응답 모델
└── services/         # 시장, 모의투자, 전략 서비스
```

## 모의투자 API

- `GET /api/v1/paper/accounts`
- `GET /api/v1/paper/orders`
- `GET /api/v1/paper/positions`
- `GET /api/v1/portfolios/summary`
- `POST /api/v1/paper/orders`

시장가 주문은 데모 시세로 즉시 체결합니다. 지정가 주문도 현재 단계에서는 요청
가격으로 즉시 체결하며, 수수료율은 `PAPER_FEE_RATE`로 설정합니다. 계좌 잠금부터
현금·수량 검증, 주문, 체결, 현금 원장, 포지션과 스냅샷 기록까지 하나의 DB
트랜잭션으로 처리합니다.

## 설계 원칙

- 금융·세금 계산은 버전이 기록되는 규칙 엔진에서 결정적으로 수행합니다.
- AI는 근거 검색과 설명을 담당하고 계산 결과를 임의로 만들지 않습니다.
- 실제 시세, 모의 주문, 실전 증권 주문은 서로 다른 모듈로 분리합니다.
- 주문 요청은 `idempotency_key`를 필수로 받으며, 영속 원장 단계에서 유일 제약으로 중복 처리를 막습니다.
- 금액과 수량은 `float`가 아니라 `Decimal`/PostgreSQL `NUMERIC`을 사용합니다.
- 한투 API 키는 서버 환경변수에만 보관합니다.
