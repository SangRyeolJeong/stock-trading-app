# MOA

주식 시세·모의투자·포트폴리오에 절세 계산과 근거 기반 투자전략을 결합하는
데스크톱 우선 투자 애플리케이션입니다.

## 현재 구현 범위

- React Router 기반 6개 독립 화면
- TanStack Query 기반 시세 및 전략 서버 상태
- FastAPI 데모 시세 REST API
- QQQM 실시간 데모 WebSocket
- 환경변수 전환형 한국투자증권 국내·해외 현재가와 USD/KRW 환율
- 2026년 규칙 버전 기반 ISA·연금저축·IRP·해외직투 절세 비교
- PostgreSQL·SQLAlchemy 2.0 기반 모의투자 원장과 멱등 주문 API
- 원화·달러 잔액, 즉시 체결, 포지션, 평균단가와 실현손익
- DB 원장 기반 포트폴리오와 주문 내역 화면
- 규칙 기반 전략 추천 API
- 한투 REST 클라이언트 경계
- FastAPI 테스트 및 Ruff 검사

## 실행

### 1. 백엔드

Windows PowerShell:

```powershell
cd D:\programming\backend
py -3.12 -m venv .venv-win
.\.venv-win\Scripts\python -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python -m alembic upgrade head
.\.venv-win\Scripts\python -m pytest
.\.venv-win\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

### 2. 프론트엔드

```bash
cd /mnt/d/programming/frontend
npm install
npm run dev
```

접속:

- 앱: `http://localhost:5173`
- API 문서: `http://localhost:8000/docs`

실제 한국투자증권 시세를 사용할 때는 `backend/.env`에
`MARKET_DATA_PROVIDER=kis`, `KIS_APP_KEY`, `KIS_APP_SECRET`을 설정합니다.

## 검증

```bash
cd frontend
npm run build
npm run lint
```

```powershell
cd D:\programming\backend
.\.venv-win\Scripts\python -m pytest
.\.venv-win\Scripts\python -m ruff check app tests
```

## 핵심 원칙

```text
사용자 입력
→ 절세 계산 엔진
→ 전략 규칙 엔진
→ ETF 데이터 조회
→ 근거 문서 조회
→ AI 설명 생성
```

AI가 세율·수익률·ETF 보수를 임의로 생성하지 않도록 계산과 설명을 분리합니다.
절세 계산 응답에는 적용 규칙 버전, 공식 근거 URL과 계산 가정이 함께 포함됩니다.
