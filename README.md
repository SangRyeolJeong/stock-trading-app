# MOA

주식 시세·모의투자·포트폴리오에 절세 계산과 근거 기반 투자전략을 결합하는
데스크톱 우선 투자 애플리케이션입니다.

## 현재 구현 범위

- React Router 기반 6개 독립 화면
- TanStack Query 기반 시세 및 전략 서버 상태
- FastAPI 데모 시세 REST API
- QQQM 실시간 데모 WebSocket
- 멱등성 키를 포함한 모의 주문 API
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
