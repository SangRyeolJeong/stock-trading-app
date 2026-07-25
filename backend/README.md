# MOA API

FastAPI 기반의 MOA 백엔드입니다. 비동기 시세 스트림, 모의 주문, 포트폴리오,
절세 계산 및 전략 추천을 제공하는 것을 목표로 합니다.

현재는 한투 API 키 없이도 프론트엔드 개발과 테스트가 가능하도록
`MockMarketDataProvider`가 기본값입니다.

## 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest
uvicorn app.main:app --reload --port 8000
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
├── integrations/kis/ # 한국투자증권 경계
├── schemas/          # 요청·응답 모델
└── services/         # 시장, 모의투자, 전략 서비스
```

## 설계 원칙

- 금융·세금 계산은 버전이 기록되는 규칙 엔진에서 결정적으로 수행합니다.
- AI는 근거 검색과 설명을 담당하고 계산 결과를 임의로 만들지 않습니다.
- 실제 시세, 모의 주문, 실전 증권 주문은 서로 다른 모듈로 분리합니다.
- 주문 요청은 `idempotency_key`로 중복 처리를 막습니다.
- 금액과 수량은 `float`가 아니라 `Decimal`/PostgreSQL `NUMERIC`을 사용합니다.
- 한투 API 키는 서버 환경변수에만 보관합니다.
