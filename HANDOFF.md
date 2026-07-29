# MOA Codex handoff

마지막 갱신: 2026-07-29
현재 기준 저장소: `/home/user/code/stock-trading-app`

## 새 Codex가 먼저 확인할 것

```bash
cd /home/user/code/stock-trading-app
pwd
git status -sb
git log --oneline -5
```

그다음 `AGENTS.md`, 이 문서, `README.md`, `backend/README.md`,
`SECURITY.md`를 읽고 작업을 시작한다.

## 현재 Git 상태

- 원격: `https://github.com/SangRyeolJeong/stock-trading-app.git`
- 기준 브랜치: `main`
- 이번 작업의 시작 커밋: `fe392be` (`Merge pull request #1`)
- 기능 구현 커밋:
  - `84f9c9d` — MOA 화면과 실데이터 API 연결
  - `1014afc` — KIS 시장 터미널 구현
  - `c6d0427` — 구조화 전략 추천 엔진
  - `efd6694` — SQLite 호환 원장 마이그레이션 수정
- WSL 이전 직후 추적 파일 변경은 없었다.
- 이후 WSL 문서화, CI, ESLint, 인증·사용자 격리, 컨테이너화와 레거시
  정리를 한 작업 묶음으로 검증했다.

현재 커밋은 `git log -1 --oneline`, 정확한 파일 상태는
`git status -sb`로 확인한다.

## 2026-07-29에 완료한 환경 이전

- 개발 기준 경로를 `/mnt/d/programming`에서
  `/home/user/code/stock-trading-app`으로 옮겼다.
- 원격 `main`을 새로 복제했으며 기존 D 드라이브 사본은 삭제하지 않았다.
- 기존 `backend/.env`를 내용 출력 없이 새 복제본으로 이전하고 권한을 `600`으로 설정했다.
- `uv 0.12.0`을 `~/.local/bin`에 설치했다.
- `backend/.venv`에 CPython `3.12.13`과 `requirements-dev.txt` 의존성을 설치했다.
- `frontend`에서 `npm ci`로 Linux용 의존성을 새로 설치했다.
- VS Code의 `stock-trading-app [WSL: Ubuntu]` 새 창을 열었다.

현재 개발은 새 WSL 경로에서만 진행한다. `/mnt/d/programming`은 사용자가
정리 여부를 결정하기 전까지 보존한다.

## 마지막 검증 결과

2026-07-29 새 WSL 복제본에서 확인:

```text
backend pytest: 67 passed
backend Ruff: All checks passed
frontend Vitest: 7 passed
frontend build: passed
frontend ESLint: passed
Alembic upgrade to 20260729_0002: passed
local smoke test: passed
git diff check: passed
```

로컬 스모크 테스트는 Mock 시장 데이터와 임시 SQLite DB를 사용해 백엔드와
프론트엔드를 함께 실행했다. 프론트 HTML/모듈 제공, 현재가·차트·호가·검색·
기업정보, 절세·전략 API, 시장가 체결, 주문 멱등성, 포트폴리오 반영, 지정가
대기와 취소를 확인했다. 실제 KIS와 PostgreSQL 연결은 이 테스트 범위에
포함하지 않았다. 인증 경계 변경 후에는 계좌 ID 없는 주문·포트폴리오 반영과
클라이언트 계좌 ID 주입의 422 거부도 다시 확인했다. 실제 Supabase 프로젝트의
로그인과 토큰 검증은 자격정보가 없어 포함하지 않았다.

재검증 명령:

```bash
cd /home/user/code/stock-trading-app/backend
.venv/bin/python -m pytest
.venv/bin/python -m ruff check app tests

cd /home/user/code/stock-trading-app/frontend
npm test
npm run build
npm run lint
```

## 현재 구현 범위 요약

- React Router 기반 홈, 종목, 절세, 전략, 포트폴리오, 설정, 학습 화면
- TanStack Query 기반 API 상태 관리
- FastAPI 시장 데이터 REST/WebSocket API
- Mock/KIS 전환형 국내·해외 현재가, 환율, 종목 검색, 차트, 호가, 기업 개요
- PostgreSQL·SQLAlchemy 기반 모의투자 원장
- 데모/Supabase 전환형 인증과 사용자별 모의 계좌·원장 격리
- Supabase 이메일·비밀번호 로그인/회원가입 및 API Bearer 토큰 연결
- 시장가/지정가 주문, 자동 체결, 취소, 현금·수량 예약, 평균단가와 실현손익
- 포트폴리오 및 주문 내역 API/화면
- `KR-2026.07` 절세 비교 엔진
- `STRATEGY-2026.07` 구조화 전략 추천 엔진
- 공식 근거가 연결된 투자 학습 콘텐츠와 로컬 진도
- 로컬 사용자 설정과 통합 검색

세부 API와 설계는 `README.md`와 `backend/README.md`를 기준으로 확인한다.

## 실행 방법

백엔드:

```bash
cd /home/user/code/stock-trading-app/backend
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

프론트엔드:

```bash
cd /home/user/code/stock-trading-app/frontend
npm run dev
```

- 앱: `http://localhost:5173`
- API 문서: `http://localhost:8000/docs`
- 기본 시장 데이터 공급자는 Mock이다.
- 실제 KIS 사용 시 필요한 값은 `backend/.env.example`의 키 목록을 참고하되,
  실제 `backend/.env` 내용은 출력하거나 커밋하지 않는다.
- 기본 `DATABASE_URL`은 로컬 PostgreSQL을 가리킨다. 실제 앱을 띄우기 전에
  PostgreSQL 실행 여부와 마이그레이션 상태를 확인한다.

## 알려진 주의사항

1. ESLint 10 flat config 전환 후 `npm audit`의 high severity 경고는
   16건에서 2건으로 줄었다. 남은 두 집계는 현재 사용하지 않는 React Router
   RSC/서버 액션 경로의 같은 권고이며 자세한 판단은 `SECURITY.md`에 있다.
   `npm audit fix --force`는 실행하지 않았다.
2. 이 WSL에는 Docker가 설치돼 있지 않았다. 현재 FastAPI/React 검증에는
   필요하지 않았지만 컨테이너 이미지 빌드는 Docker가 있는 환경에서 확인해야 한다.
3. GitHub 기여 그래프는 WSL 또는 저장소 공개/비공개 여부만으로 결정되지 않는다.
   커밋 작성자 이메일이 GitHub 계정 이메일과 연결돼 있고, 커밋이 기본 브랜치에
   포함돼 있는지 확인해야 한다.

## 추천 다음 작업 순서

아래는 확정된 제품 요구사항이 아니라, 현재 코드 상태를 바탕으로 한 우선순위 제안이다.
새 작업을 시작하기 전 코드와 사용자 의도를 다시 확인한다.

1. 운영 PostgreSQL과 배포 환경을 구성하고 Supabase 프로젝트에서 실제
   로그인·토큰 검증을 통합 테스트한다.
2. 사용자 프로필 서버 동기화와 계정 삭제·데이터 보존 정책을 설계한다.

## CI

`.github/workflows/ci.yml`은 `main` push와 pull request에서 다음 검증을
자동 실행한다.

- Python 3.12: 백엔드 pytest와 Ruff
- PostgreSQL 17: Alembic head 적용, FastAPI `/ready`, 데모 계좌 생성
- Node.js 20: 프론트엔드 `npm ci`, 빌드와 ESLint
- Docker: Compose 설정 검증과 백엔드·프론트엔드 이미지 빌드

## 프론트엔드 린트와 의존성

- ESLint `10.8.0` flat config
- `typescript-eslint` `8.65.0`
- `eslint-plugin-react-hooks` `7.1.1`
- `eslint-plugin-react-refresh` `0.5.3`
- 최신 Hooks 권장 규칙에서 발견된 동기식 effect 상태 갱신 6건을 제거했다.
- 프론트엔드 빌드와 ESLint가 갱신된 구성에서 통과한다.

## 레거시 골격 정리

현재 실행·빌드·문서 참조를 조사한 뒤 다음 초기 프로토타입 잔여물을 제거했다.

- 실행 스크립트와 소스가 없던 루트 Node `package.json`과 lockfile
- FastAPI와 별개였던 Spring Boot용 Gradle 파일과 `backend/src` Java 골격
- Supabase Auth 대신 자체 비밀번호 테이블을 정의하던 미사용 초기 SQL 스키마

현재 애플리케이션 구성은 `frontend`의 React/Vite와 `backend`의
FastAPI/Python으로 단일화됐다.

## 인증과 사용자별 원장

- 개발 기본값은 `AUTH_MODE=demo`와 `VITE_AUTH_MODE=demo`다.
- 운영 백엔드는 Supabase 인증 설정 없이는 시작하지 않는다.
- Supabase 모드에서 프론트는 로그인/회원가입과 세션 갱신을 처리하고 access
  token을 API 요청에 첨부한다.
- 백엔드는 Supabase Auth `get_user(jwt)`로 토큰을 검증한다.
- 클라이언트의 `account_id` 입력을 제거하고 서버가 사용자별 계좌를 결정한다.
- `paper_accounts.user_id`에는 단일 계좌 unique constraint를 추가했다.
- 사용자 A/B의 계좌·주문·포지션 격리와 계좌 ID 주입 거부를 테스트한다.
- 코드에서 사용하지 않던 Redis 설정과 Python 의존성을 제거했다.

## 컨테이너 실행

- 루트 `compose.yaml`은 PostgreSQL 17, FastAPI, Nginx 정적 프론트엔드를
  Mock 시세·데모 인증으로 실행한다.
- 백엔드 이미지는 Python 3.12 non-root 사용자로 실행하고 시작 시 Alembic
  마이그레이션을 적용한다.
- 프론트엔드는 Node 20 빌드 후 Nginx 1.29에서 SPA fallback과 기본 보안
  헤더를 적용해 제공한다.
- 현재 WSL에는 Docker가 없으므로 로컬 이미지 빌드는 실행하지 못했으며 CI에서
  Compose 검증과 두 이미지를 빌드하도록 추가했다.
- `docs/DEPLOYMENT.md`에 운영 환경변수, Supabase/KIS 비밀 경계, 단일
  migration job, 상태 확인, 백업 및 출시 전 정책 결정을 정리했다.

## 새 Codex에 전달할 시작 문장

```text
/home/user/code/stock-trading-app에서 AGENTS.md와 HANDOFF.md를 먼저 전부 읽고,
README.md, backend/README.md, SECURITY.md와 git 상태를 확인해.
기존 변경과 backend/.env는 건드리지 말고, HANDOFF의 현재 상태를 검증한 뒤
내가 요청하는 다음 작업을 진행해.
```
