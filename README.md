# MOA

주식 시세·모의투자·포트폴리오에 절세 계산과 근거 기반 투자전략을 결합하는
데스크톱 우선 투자 애플리케이션입니다.

## 현재 구현 범위

- React Router 기반 8개 독립 화면
- TanStack Query 기반 시세 및 전략 서버 상태
- FastAPI 데모 시세 REST API
- QQQM 실시간 데모 WebSocket
- 환경변수 전환형 한국투자증권 국내·해외 현재가와 USD/KRW 환율
- KIS 종목 마스터 기반 종목 검색과 국내 10단계·해외 최우선 호가
- QQQM·QQQ·SPY·VOO와 KODEX·TIGER 미국S&P500·미국나스닥100의
  공식 스냅샷 기반 보수·상위 구성종목 중복도 및 상장국 비교
- 2026년 규칙 버전 기반 ISA·연금저축·IRP·해외직투 절세 비교
- PostgreSQL·SQLAlchemy 2.0 기반 모의투자 원장과 멱등 주문 API
- 원화·달러 잔액, 시장가 체결, 지정가 대기·자동 체결·취소, 평균단가와 실현손익
- DB 원장 기반 포트폴리오와 주문 내역 화면
- 주문 전 종목 비중·투자자산·잔여 현금 변화 계산과 포트폴리오 집중도 진단
- 실제 보유 비중과 맞춤 목표 비중의 차이를 반영한 다음 월 투자금 리밸런싱 계산
- 리밸런싱 주식성 배분액을 현재가·환율·수수료로 정수 ETF 주문 초안에 연결
- 목표·기간·위험성향·선호 조건을 반영하는 구조화 전략 추천 API와 실행 계획
- 물가·현재가치 목표·연 투자금 증액을 반영한 목표 계산과 시나리오 관리·비교
- 저장 시나리오를 진행 목표로 지정해 홈 현황과 맞춤 자산배분 조건으로 연결
- 공식 근거가 연결된 투자 학습 콘텐츠와 로컬 진도·이어보기
- 종목과 주요 기능을 함께 찾는 키보드 지원 통합 검색
- 이름·투자금·기간·수익률·위험성향을 공유하는 사용자별 설정과 로컬 폴백
- 홈과 종목 탐색이 즉시 공유하는 사용자별 관심종목 추가·해제·복원
- 한투 REST 클라이언트 경계
- FastAPI 테스트 및 Ruff 검사

## 실행

현재 기준 개발 환경은 WSL Ubuntu이며 저장소 경로는
`/home/user/code/stock-trading-app`입니다. 백엔드와 프론트엔드는 각각
WSL 안의 Linux용 의존성을 사용합니다.

### 1. 백엔드

```bash
cd /home/user/code/stock-trading-app/backend
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

처음 환경을 구성하는 경우에는 [backend/README.md](backend/README.md)의
Python 3.12 가상환경과 환경변수 설정 절차를 먼저 따릅니다. 기본
`DATABASE_URL`은 로컬 PostgreSQL을 사용하므로 서버 실행 전 PostgreSQL과
마이그레이션 상태를 확인해야 합니다. 시장 데이터 공급자는 기본적으로 Mock이며,
KIS 키 없이도 개발할 수 있습니다.

### 2. 프론트엔드

```bash
cd /home/user/code/stock-trading-app/frontend
npm ci
npm run dev
```

이미 `node_modules`가 구성되어 있다면 다음 실행부터는 `npm run dev`만
사용하면 됩니다.

접속:

- 앱: `http://localhost:5173`
- API 상태: `http://localhost:8000/health`
- API 준비 상태(DB 포함): `http://localhost:8000/ready`
- API 문서: `http://localhost:8000/docs`

실제 한국투자증권 시세를 사용할 때는 `backend/.env`에
`MARKET_DATA_PROVIDER=kis`, `KIS_APP_KEY`, `KIS_APP_SECRET`을 설정합니다.
실제 키는 프론트엔드 환경변수에 두거나 Git에 커밋하지 않습니다.

기본 인증 모드는 로컬 개발용 `demo`입니다. 사용자별 계정으로 실행하려면
백엔드와 프론트엔드에 같은 Supabase 프로젝트를 설정합니다.

```text
# backend/.env
AUTH_MODE=supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...

# frontend/.env.local
VITE_AUTH_MODE=supabase
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

운영 환경은 `AUTH_MODE=supabase`가 아니면 백엔드가 시작되지 않습니다.
publishable key는 Supabase가 브라우저 사용을 허용한 공개 키이며,
secret/service-role 키는 프론트엔드에 넣지 않습니다.

Supabase 로그인 모드에서는 설정 화면의 투자 기본값을
`GET/PUT /api/v1/me/preferences`로 사용자별 저장합니다. 사용자마다
브라우저 캐시 키도 분리되며, 일시적인 연결 오류가 있어도 로컬 설정은
유지됩니다. 데모 모드는 기존처럼 현재 브라우저에만 저장합니다.

### 컨테이너로 로컬 실행

Docker가 설치된 환경에서는 Mock 시세·데모 인증·PostgreSQL 구성을 한 번에
실행할 수 있습니다.

```bash
cd /home/user/code/stock-trading-app
docker compose up --build
```

앱은 `http://localhost:5173`, API는 `http://localhost:8000`에서 열립니다.
`compose.yaml`의 DB 비밀번호는 로컬 개발 전용입니다. 운영 배포에서는 관리형
PostgreSQL과 별도 비밀 저장소를 사용하고, 프론트 이미지를 빌드할 때 Supabase
관련 `VITE_*` build argument를 지정해야 합니다.

운영 환경변수, 마이그레이션 순서와 출시 전 보안 점검은
[배포 가이드](docs/DEPLOYMENT.md)를 따릅니다.

## 검증

```bash
cd /home/user/code/stock-trading-app/backend
.venv/bin/python -m pytest
.venv/bin/python -m ruff check app tests
```

```bash
cd /home/user/code/stock-trading-app/frontend
npm test
npm run build
npm run lint
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
