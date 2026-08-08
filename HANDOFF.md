# MOA Codex handoff

마지막 갱신: 2026-07-30
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

2026-08-08 목표 계획 현실화 번들 검증:

```text
backend pytest: 113 passed
backend Ruff: All checks passed
frontend Vitest: 48 passed
frontend build: passed
frontend ESLint: passed
git diff check: passed
```

목표 계산 API에 현재가치 목표, 물가상승률과 연 투자금 증액률을 추가하고 기존
요청의 기본값, 기존 공유 링크와 이름 없는 로컬 저장본의 호환성을 함께
검증했다. 실제 시장·인증·운영 PostgreSQL 연결은 이 변경의 검증 범위가 아니다.

2026-07-30 새 WSL 복제본에서 확인:

```text
backend pytest: 79 passed
backend Ruff: All checks passed
frontend Vitest: 30 passed
frontend build: passed
frontend ESLint: passed
Alembic upgrade to 20260729_0003: passed
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

2026-07-30에는 `/market` 기본 진입 경로와 관심종목 편집 흐름을 추가로
검증했다. 사용자별 로컬 관심목록, 종목 기호 정규화·중복 제거, 추가·해제,
기본 목록 복원 테스트를 포함하며 Mock 종목 목록과 QQQM 현재가 API 응답도
확인했다.

같은 날 `ETF-COMPARE-2026.07` 비교 엔진과 종목 화면의 ETF 비교 탭도
검증했다. QQQM·QQQ·SPY·VOO 공식 스냅샷, 상위 구성종목 중복도, 1천만원당
연간 보수 차이, 공통 종목, 공식 출처와 학습·모의주문 연결을 포함한다.

이후 모의주문 창에 실제 포트폴리오 원장과 USD/KRW 환율을 연결한 주문 영향
계산을 추가했다. 매수·매도 예상 금액에 따라 주문 후 종목 비중, 투자자산,
해당 통화 현금을 미리 보여주며 25%·40% 집중도 구간을 구분한다. 포트폴리오
화면에는 현금 완충 비중과 최대 종목 비중 진단, 절세·전략 계산기 이동 경로를
추가했다.

포트폴리오와 `STRATEGY-2026.07` 목표 비중도 연결했다. 현재 지원 종목을
주식성 자산으로 분류하고 현금·방어 자산과 함께 현재/목표 차이를 계산한 뒤,
매도 없이 다음 월 투자금만 부족한 자산군에 비례 배분하는 계획을 표시한다.

주식성 자산 제안액은 QQQM 현재가와 USD/KRW 환율, 모의 수수료 0.1%를
사용해 매수 가능한 정수 수량으로 변환한다. 포트폴리오에서 실행 예시 수량을
선택하면 시장 주문창에 초안 수량이 채워진다. 이는 확정 상품 추천이 아니며
모의 원장의 USD 잔액을 자동 환전하지 않는다.

ETF 비교 범위에는 KODEX 미국S&P500(379800)과 미국나스닥100(379810)을
추가했다. 삼성자산운용 공식 상품 페이지의 2026-07-03·07-08 스냅샷을
사용하며 상장국·거래통화를 응답과 화면에 표시한다. 한국·미국 교차상장
비교에서는 명목 총보수 외에 세금·환전·거래시간·기타비용이 다르다는 경고를
별도로 보여준다.

이어서 미래에셋자산운용의 2025-07-31 공식 월간운용보고서를 근거로
TIGER 미국S&P500(360750)과 미국나스닥100(133690)도 비교 프로필에
추가했다. 같은 국내 상장·같은 지수인 TIGER와 KODEX를 바로 비교할 수 있으며,
1천만원당 명목 총보수 차이와 상위 종목 중복도를 기존 공식 계산식으로 제공한다.

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
- 사용자별 투자 기본 설정 API와 계정별 브라우저 캐시·서버 동기화
- 홈·시장 화면이 공유하는 사용자별 관심종목과 URL 기반 시장 탐색 탭
- 미국상장 4종과 국내상장 KODEX·TIGER 4종의 공식 운용사 스냅샷 기반 ETF
  보수·상위 구성종목 중복도·상장국 비교
- 시장가/지정가 주문, 자동 체결, 취소, 현금·수량 예약, 평균단가와 실현손익
- 포트폴리오 및 주문 내역 API/화면
- 실제 보유 원장 기반 주문 전 포트폴리오 영향 계산과 집중도 진단
- 전략 목표 대비 현재 비중 차이와 다음 월 투자금 리밸런싱 제안
- 리밸런싱 제안액 기반 QQQM 정수 수량 계산과 모의주문 초안 전달
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

1. ETF 운용사 자료 수집을 자동화하고 현재 400일인 CI 신선도 한도를 자료별
   갱신 주기에 맞게 단축한다.
2. 방어·인컴 자산군의 상품 메타데이터와 Mock 시세를 추가해 리밸런싱 실행
   초안을 주식성 외 자산군으로 확장한다.
3. 운영 PostgreSQL과 배포 환경을 구성하고 Supabase 프로젝트에서 실제
   로그인·토큰 검증을 통합 테스트한다.
4. 계정 삭제 시 설정·모의투자 원장의 삭제 또는 보존 정책을 확정하고
   사용자 데이터 삭제 흐름을 구현한다.

## CI

`.github/workflows/ci.yml`은 `main` push와 pull request에서 다음 검증을
자동 실행한다.

- Python 3.12: 백엔드 pytest와 Ruff
- PostgreSQL 17: Alembic head 적용, FastAPI `/ready`, 데모 계좌·설정 생성
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

## 사용자 설정 서버 동기화

- `GET/PUT /api/v1/me/preferences`가 현재 인증 사용자별 투자 기본 설정을
  조회하고 저장한다.
- DB와 Pydantic 양쪽에서 숫자 범위, 전략 목표, 위험성향과 알 수 없는 필드를
  검증한다.
- 프론트는 Supabase 로그인 사용자의 로컬 캐시 키를 계정별로 분리해 다른
  사용자의 설정이 잠깐 노출되거나 섞이지 않게 한다.
- 서버 설정을 우선 불러오고, 최초 사용자면 계정별 로컬 기본값으로 생성한다.
- 설정 변경은 600ms 동안 모아 저장하며 네트워크 오류가 있어도 로컬 값을
  유지하고 설정 화면에 동기화 상태를 표시한다.
- 데모 인증에서는 이전과 같이 브라우저 로컬 설정만 사용한다.
- Alembic `20260729_0003`, 사용자 격리·검증 API 테스트, 로컬 범위·초기화·
  지연 저장 프론트 테스트를 추가했다.

## 시장 진입과 관심종목

- 홈의 관심종목 편집 버튼과 전략의 모의투자 CTA가 더 이상 존재하지 않는
  경로로 떨어지지 않도록 `/market` 기본 경로를 추가했다.
- 기본 진입 종목은 QQQM이며 `?tab=favorites|domestic|overseas|etf`로
  종목 탐색 탭을 URL에 유지한다.
- 홈과 시장 화면의 중복 로컬 저장 코드를 공용 외부 저장소로 통합해 별표
  추가·해제가 홈 관심목록에 즉시 반영된다.
- Supabase 사용자마다 관심목록 캐시 키를 분리하고 데모 모드는 기존 로컬
  캐시를 사용한다.
- 종목 기호를 대문자로 정규화하고 유효하지 않은 값과 중복을 제거하며 최대
  50개로 제한한다. 모두 해제한 경우 기본 관심목록 복원 버튼을 제공한다.

## ETF 비교

- `GET /api/v1/markets/etfs`와 `GET /api/v1/markets/etfs/compare`가
  QQQM·QQQ·SPY·VOO의 버전된 공식 운용사 스냅샷을 제공한다.
- 중복도는 표시된 상위 종목에서 공통 종목별 두 비중의 최솟값을 합산한 뒤,
  두 ETF 중 더 작은 표시 비중 합계로 정규화한다. 응답에 계산식을 포함한다.
- 총보수 차이는 1천만원을 동일하게 투자했을 때의 단순 연간 비용 차이로
  계산하고 수익률·환율·거래비용은 섞지 않는다.
- 각 ETF에 상품 정보와 구성종목 기준일, 운용사 공식 URL을 별도로 기록한다.
- 시장 화면은 같은 기초지수 ETF를 기본 비교 대상으로 고르고, 결과에서
  상대 ETF 종목·모의주문과 `qqq-vs-qqqm` 학습 콘텐츠로 이동할 수 있다.
- Mock 공급자에 QQQ·SPY·VOO 시세를 추가해 기본 ETF 목록에서 종목을
  선택해도 차트와 모의주문 흐름이 끊기지 않는다.
- KODEX 미국S&P500(379800)과 미국나스닥100(379810)은 삼성자산운용
  공식 상품 페이지의 총보수·구성종목을 사용한다. 각각 2026-07-03,
  2026-07-08 기준이며 원문 URL을 응답에 포함한다.
- ETF 프로필에 `listing_country`와 `trading_currency`를 추가했다. 상장국이
  다른 비교는 같은 기초지수라도 과세·환전·거래시간과 기타비용을 함께
  확인하라는 설명을 덧붙인다.
- KODEX 2종과 기존 목록에만 있던 TIGER 미국나스닥100(133690)의 Mock
  현재가를 추가해 종목·차트·모의주문 흐름이 404로 끊기지 않는다.
- 비교하는 보수는 각 운용사 페이지에 표시된 명목 총보수다. 합성총보수,
  기타비용, 매매중개수수료와 세금은 연간 차이 계산에 포함하지 않으며
  화면과 API 면책문구에 이 한계를 명시한다.
- 공식 상품·구성종목 기준일 중 하나라도 현재보다 미래이거나 400일 넘게
  오래되면 백엔드 테스트가 실패해 CI에서 스냅샷 갱신 필요를 알린다.
- TIGER 미국S&P500(360750)과 미국나스닥100(133690)은 미래에셋
  공식 2025-07-31 월간운용보고서의 총보수와 상위 10종목을 사용한다.
  동일 지수 KODEX와의 국내 운용사 간 비교도 같은 API·UI에서 지원한다.

## 주문 전 포트폴리오 영향

- 종목 주문 창은 별도 잔액 스냅샷 대신 `GET /api/v1/portfolios/summary`의
  실제 모의 원장을 사용한다.
- KRW·USD 보유 종목을 현재 USD/KRW 환율로 합산한 뒤 예상 체결 금액을
  더하거나 빼서 주문 후 투자자산과 해당 종목 비중을 계산한다.
- 예상 수수료는 투자자산 비중이 아니라 주문 후 현금에 반영하며, 이는 주문
  전 단순 예상치이고 지정가의 실제 체결가격 차이는 체결 후 원장에 반영된다.
- 단일 종목 비중 25% 이상은 점검, 40% 이상은 집중 경고로 표시한다. 이
  기준은 세법이나 투자 권고가 아니라 사용자가 분산 여부를 점검하기 위한 UI
  기준이다.
- 주문 창에서 포트폴리오 상세, 세후 계좌 비교, 맞춤 전략으로 이동할 수 있고
  포트폴리오 화면에서도 현금 완충·최대 종목 비중을 확인할 수 있다.

## 보유 비중 기반 리밸런싱

- 포트폴리오 화면이 사용자 설정으로 전략 추천 API를 호출해 주식성·방어·
  현금성 자산의 목표 비중을 가져온다.
- 현재 앱에서 거래 가능한 주식과 주식 ETF는 모두 주식성 자산으로 분류하고,
  별도 방어 자산 보유는 아직 0으로 본다. 채권 ETF 분류가 추가되면 종목
  메타데이터 기반 분류로 교체해야 한다.
- 다음 월 투자금을 더한 예상 총자산에서 자산군별 목표 금액 부족분을 계산한
  후 부족분 비율대로 투자금을 배분한다. 비중이 초과된 자산군에는 0원을
  제시하며 매도나 세금·거래비용은 계산하지 않는다.
- 신규 포트폴리오는 목표 비중대로 배분하고, 원 단위 반올림 뒤에도 세 자산군
  제안액 합계가 월 투자금과 정확히 같도록 마지막 자산군에서 잔액을 맞춘다.
- 주식성 제안액은 QQQM을 실행 예시로 삼아 `현재가 × USD/KRW × (1+0.1%
  수수료)`로 한 주 비용을 계산하고 정수 수량만 제안한다.
- 남는 금액과 현재가 환산액을 함께 표시하고, 주문 화면 URL의
  `draftQuantity`를 통해 초안 수량을 전달한다. 주문 화면은 1~100,000 범위의
  정수만 받아 비정상 URL 입력을 제한한다.
- 이 단계는 환전·소수점 거래를 수행하지 않는다. 실제 모의 체결 가능 여부는
  주문 화면의 USD 현금과 최신 시세 검증이 최종 결정한다.

## 투자 목표 계산과 시나리오 비교

- `GOAL-2026.08.2` 엔진이 현재 자산·목표 금액·첫해 월 투자금·기간·예상
  수익률·물가상승률·연 투자금 증액률로 예상 자산, 현재가치, 목표 달성률,
  필요 첫해 월 투자금과 수익률 민감도를 계산한다.
- 목표 금액은 만기 명목금액 또는 현재 구매력 기준으로 선택한다. 현재 구매력
  기준이면 입력 물가상승률로 만기 명목 목표를 환산해 달성률을 계산한다.
- 계산 입력은 URL fragment 공유 링크로 재현할 수 있고 결과는 브라우저 로컬
  저장소에 최대 10개까지 보관한다. 서버나 계정에는 동기화하지 않는다.
- 저장할 때 40자 이내 이름을 붙이고 이후 수정할 수 있다. 기존 이름 없는
  저장본에는 목표 금액과 기간을 조합한 기본 이름을 표시한다.
- 저장한 시나리오 중 2개를 선택하면 현재 자산·목표·물가·증액 조건과 저장
  당시 적용 목표·예상 자산·현재가치·달성률·필요 월 투자금을 비교할 수 있다.
- 목표 금액이나 기간이 다르면 달성률만으로 계획의 우열을 판단할 수 없다는
  안내를 표시한다. 선택 항목을 삭제하면 비교 상태에서도 즉시 제거한다.

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
