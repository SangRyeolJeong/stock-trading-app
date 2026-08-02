# MOA API

FastAPI 기반의 MOA 백엔드입니다. 비동기 시세 스트림, 모의 주문, 포트폴리오,
절세 계산 및 전략 추천을 제공하는 것을 목표로 합니다.

현재는 한투 API 키 없이도 프론트엔드 개발과 테스트가 가능하도록
`MockMarketDataProvider`가 기본값입니다. 주문은 PostgreSQL 원장에 영속화되며,
개발 기본값에서는 데모 사용자의 원화·달러 초기 잔액이 첫 조회 또는 주문 시
생성됩니다. Supabase 인증 모드에서는 검증된 사용자별로 독립 계좌와 원장이
생성됩니다.

`MARKET_DATA_PROVIDER=kis`로 변경하면 한국투자증권 REST API에서 국내·해외
현재가와 USD/KRW 환율을 조회합니다. 앱 키가 없을 때 서버가 실수로 KIS 모드로
실행되지 않도록 시작 단계에서 설정 오류를 발생시킵니다.

## 로컬 실행

현재 기준 개발 환경은 `/home/user/code/stock-trading-app`의 WSL Ubuntu와
Linux CPython 3.12입니다. 이 저장소에 이미 구성된 `.venv`가 있다면 바로
활성화할 수 있습니다.

```bash
cd /home/user/code/stock-trading-app/backend
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

처음 구성하거나 가상환경을 다시 만드는 경우에는 WSL에서 `uv`를 사용합니다.

```bash
cd /home/user/code/stock-trading-app/backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
cp -n .env.example .env
chmod 600 .env
```

`cp -n`은 기존 `.env`를 덮어쓰지 않습니다. 실제 키는 `.env.example`이 아닌
`backend/.env`에만 저장하며 출력하거나 커밋하지 않습니다.

## 인증과 사용자별 원장

개발 기본값은 `AUTH_MODE=demo`이며 기존 `demo-account`를 사용합니다.
Supabase Auth를 연결할 때는 다음 서버 환경변수를 설정합니다.

```text
AUTH_MODE=supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

Supabase 모드에서는 `Authorization: Bearer <access-token>`이 필요합니다.
백엔드는 Supabase Auth 서버의 `get_user(jwt)`로 토큰을 검증하고 검증된
사용자 ID로 계좌를 결정합니다. 주문 요청과 조회 URL은 `account_id`를 받지
않으므로 클라이언트가 다른 사용자의 계좌를 선택할 수 없습니다.

`APP_ENV=production`에서는 `AUTH_MODE=supabase`와 Supabase URL/publishable
key가 모두 없으면 설정 오류로 시작을 중단합니다. Supabase URL과
`CORS_ORIGINS`는 공개 HTTPS 주소여야 하며 wildcard, localhost, URL 경로를
허용하지 않습니다. secret/service-role 키는 이 검증에 필요하지 않으며
브라우저나 로그에 노출하지 않습니다. `MARKET_DATA_PROVIDER=kis`를 선택하면
KIS app key와 app secret도 시작 전에 검증합니다.

기본 `DATABASE_URL`은 로컬 PostgreSQL의 `moa` 데이터베이스를 가리킵니다.
PostgreSQL을 준비한 뒤 마이그레이션을 적용합니다.

서버는 기본적으로 인스턴스당 영구 연결 5개와 일시 초과 연결 5개까지만
허용합니다. 풀 대기 10초, 연결 10초, 쿼리 30초 제한을 적용하고 30분이 지난
연결은 재생성합니다. `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`,
`DATABASE_POOL_TIMEOUT_SECONDS`, `DATABASE_POOL_RECYCLE_SECONDS`,
`DATABASE_CONNECT_TIMEOUT_SECONDS`, `DATABASE_COMMAND_TIMEOUT_SECONDS`로
조정할 수 있습니다. 전체 최대 연결 수는 대략
`인스턴스 수 × (POOL_SIZE + MAX_OVERFLOW)`이므로 DB 한도보다 낮게 잡습니다.
운영 환경은 실수로 SQLite가 사용되지 않도록 `postgresql+asyncpg://` URL만
허용합니다.

```bash
cd /home/user/code/stock-trading-app/backend
.venv/bin/python -m alembic upgrade head
```

루트 `compose.yaml`은 개발용 PostgreSQL과 일회성 `migrate` 서비스를 함께
실행합니다. `migrate`가 Alembic 적용을 성공한 뒤에만 백엔드가 시작됩니다.
백엔드 이미지는 API를 시작할 뿐 자체적으로 마이그레이션하지 않으므로, 운영
환경에서도 새 이미지로 단일 migration job을 먼저 실행해야 합니다.

운영 설정만 비밀값을 출력하지 않고 점검하려면 다음 명령을 실행합니다.

```bash
cd /home/user/code/stock-trading-app/backend
.venv/bin/python -m app.cli.deployment_preflight --config-only
```

마이그레이션까지 끝난 뒤 `--config-only`를 빼면 PostgreSQL 연결과 현재 Alembic
revision이 코드의 최신 head와 일치하는지도 확인합니다. 출력에는 환경 종류,
DB driver, CORS 주소 개수, 시세 공급자만 포함되며 URL, 비밀번호, API key,
access token은 포함되지 않습니다.

실행 후 확인:

- API 상태: `http://localhost:8000/health`
- API 준비 상태(DB 포함): `http://localhost:8000/ready`
- API 문서: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

## 검증

테스트는 별도의 SQLite DB를 사용하므로 로컬 PostgreSQL 없이도 실행할 수
있습니다.

```bash
cd /home/user/code/stock-trading-app/backend
.venv/bin/python -m pytest
.venv/bin/python -m ruff check app tests
```

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
- `DELETE /api/v1/paper/orders/{order_id}`

시장가 주문은 현재 시세로 즉시 체결합니다. 지정가는 매수 시 현재가 이하,
매도 시 현재가 이상이라는 가격 제한을 지키며, 조건이 충족되지 않으면 대기합니다.
주문 목록 조회 시 최신 시세와 대기 주문을 다시 대조하고 조건이 충족되면 현재
시세로 체결합니다. 대기 주문은 취소할 수 있고, 현금과 보유 수량은 다른 대기
주문에 예약된 금액·수량까지 반영해 검증합니다. 수수료율은 `PAPER_FEE_RATE`로
설정하며, 체결 시 주문·현금 원장·포지션·스냅샷을 하나의 DB 트랜잭션으로
처리합니다.

모든 모의투자·포트폴리오 API는 현재 인증 사용자의 계좌로 자동 범위가
제한됩니다. 데모 모드에서도 같은 서버 측 경계를 거쳐 `demo-user`로 동작합니다.

## 사용자 설정 API

- `GET /api/v1/me/preferences`
- `PUT /api/v1/me/preferences`

표시 이름, 급여·월 투자금·투자기간·예상 수익률·연금 수령 나이와 전략 선호를
검증된 사용자 ID별로 저장합니다. 아직 저장된 값이 없는 `GET` 요청은 `404`를
반환하며 프론트엔드는 해당 사용자의 로컬 기본값을 `PUT`해 최초 설정을
생성합니다. 요청은 완전한 설정 객체를 사용하고 알 수 없는 필드를 거부하므로
클라이언트가 사용자 ID를 주입할 수 없습니다.

`user_preferences.user_id`가 기본 키이며 숫자 범위와 전략·위험성향 열거값은
API 검증과 DB check constraint 양쪽에서 제한합니다. Alembic
`20260729_0003`이 테이블을 생성합니다.

## 시장 데이터 API

- `GET /api/v1/markets/quotes/{symbol}`
- `GET /api/v1/markets/instruments`
- `GET /api/v1/markets/candles/{symbol}`
- `GET /api/v1/markets/orderbooks/{symbol}`
- `GET /api/v1/markets/overview/{symbol}`
- `GET /api/v1/markets/exchange-rates/{base_currency}/{quote_currency}`
- `GET /api/v1/markets/etfs`
- `GET /api/v1/markets/etfs/compare?left=QQQM&right=QQQ`
- `WS /api/v1/markets/ws/quotes/{symbol}`

KIS 모드의 국내 현재가는 `FHKST01010100`, 해외 현재가는
`HHDFS00000300`을 사용합니다. USD/KRW는 해외 현재가 상세
`HHDFS76200200` 응답의 당일 환율을 사용합니다. 현재 지원 통화는 KRW와
USD이며, 해외 종목의 기본 거래소는 `KIS_DEFAULT_OVERSEAS_EXCHANGE`로
설정합니다. REST 기반 WebSocket 브리지는 호출 제한을 고려해 5초마다
갱신합니다.

종목 검색은 KIS가 배포하는 국내·미국 종목 마스터를 로컬 캐시하며, 마스터
다운로드가 실패하면 기본 종목 목록으로 폴백합니다. 일봉은 국내
`FHKST03010100`, 해외 `HHDFS76240000`을 사용합니다. 호가는 국내
`FHKST01010200`의 10단계 호가와 해외 `HHDFS76200100`의 최우선 1호가를
공통 응답으로 정규화합니다. 호가 REST 응답은 실시간 스트림이 아닌 조회 시점
스냅샷입니다. 기업정보는 같은 현재가 응답에서 시가·고가·저가·거래량,
52주 범위와 PER·PBR·EPS·BPS를 국내외 공통 필드로 제공합니다.

Mock 공급자는 리밸런싱 실행 예시를 위해 성장주식 QQQM 외에 배당·인컴
DGRO와 0~3개월 미국 국채 SGOV의 결정론적 데모 시세를 제공합니다. 두 상품은
기본 종목 검색, 차트·호가·기업 개요와 USD 모의주문을 지원합니다. 표시 가격과
등락은 실제 주문용 실시간 값이 아니라 개발·교육용 Mock 값입니다.

ETF 비교는 KIS 시세와 분리된 `ETF-COMPARE-2026.08` 결정론적 데이터셋을
사용합니다. 미국상장 QQQM·QQQ·SPY·VOO와 한국상장 KODEX
미국S&P500(379800)·미국나스닥100(379810), TIGER 미국S&P500(360750)·
미국나스닥100(133690)의 운용사 공식 상품·구성종목 자료 URL, 기준일,
상장국과 거래통화를 응답에 포함합니다. 상위 구성종목
중복도는 공통 종목별 두 비중의 최솟값 합계를 두 ETF 중 더 작은 상위 종목
표시 비중 합계로 나눠 계산합니다.

총보수 차이는 동일한 1천만원을 1년 보유할 때 운용사 페이지에 표시된 명목
총보수의 단순 차이입니다. 합성총보수·기타비용·매매비용·수익률·환율·세금은
포함하지 않습니다. 한국·미국 교차상장 비교는 과세·환전·거래시간 구조가
다르다는 경고를 응답 설명과 면책문구에 포함합니다.

공식 상품 정보일과 구성종목일 중 하나라도 현재보다 미래이거나 자료별 허용
기간을 초과하면 `stale_etf_symbols()` 기반 테스트가 실패합니다. 허용 기간은
일별 자료인 SPY 14일, 국내 KODEX·TIGER 45일, VOO 95일, Invesco QQQ 계열
190일이며 기존 단일 400일 한도보다 짧습니다.

KODEX·TIGER는 운용사 화면이 사용하는 공식 JSON·구성종목 API를 주 1회
자동 점검합니다. 로컬에서도 다음 명령으로 저장소 스냅샷과 공식 자료를
비교할 수 있습니다.

```bash
cd backend
python -m app.cli.check_etf_sources
python -m app.cli.check_etf_sources --check
```

첫 명령은 상태와 상위 10종목을 출력합니다. `--check`는 새 자료, 미래 기준일,
조회 오류가 있으면 실패 코드로 끝나므로 GitHub Actions 알림에 사용합니다.
도구는 금융 수치를 자동으로 덮어쓰지 않습니다. 담당자가 공식 기준일과 수치를
검토한 뒤 `app/services/etf.py`를 갱신해야 합니다. Invesco·Vanguard·State
Street는 현재 공식 페이지 형식과 접근 정책이 서로 달라 수동 검토 대상으로
남겨 둡니다.

## 절세 계산 API

- `POST /api/v1/tax/simulate`

동일한 총급여, 월 투자금, 기간, 수익률과 연금 수령 나이로 해외직투,
중개형 ISA, 연금저축펀드와 IRP를 비교합니다. 세제 숫자는
`app/tax/rules.py`의 `KR-2026.07` 규칙으로 버전 관리하며 API 응답에 공식
근거와 가정을 포함합니다.

현재 계산은 매년 말 납입, 마지막 해 일괄 처분, 수수료·환율 제외 모델입니다.
ISA는 누적 납입 1억원까지만 혜택을 적용하고 초과 금액은 해외직투로 계산합니다.
연금 세액공제 환급액은 재투자하지 않으며 정상적인 연금 수령을 가정합니다.

## 전략 추천 API

- `POST /api/v1/strategies/recommend`

목표, 투자기간, 월 투자금, 위험성향과 유동성·비용·배당 선호를 입력받아
`STRATEGY-2026.07` 규칙으로 자산군·계좌별 비중을 계산합니다. 응답에는
월 납입액, 적합도, 추천 근거 코드, 위험 요약, 실행 순서, 경고와 계산 가정이
포함됩니다.

추천 결과는 같은 입력에 항상 같은 결과를 반환하며 총 자산 비중은 100%,
자산별 월 납입액 합계는 입력 월 투자금과 일치합니다. 위험성향별 주식성 자산
상한과 유동성 선호 시 최소 현금 비중도 엔진에서 검증합니다.

## 설계 원칙

- 금융·세금 계산은 버전이 기록되는 규칙 엔진에서 결정적으로 수행합니다.
- AI는 근거 검색과 설명을 담당하고 계산 결과를 임의로 만들지 않습니다.
- 실제 시세, 모의 주문, 실전 증권 주문은 서로 다른 모듈로 분리합니다.
- 주문 요청은 `idempotency_key`를 필수로 받으며, 영속 원장 단계에서 유일 제약으로 중복 처리를 막습니다.
- 금액과 수량은 `float`가 아니라 `Decimal`/PostgreSQL `NUMERIC`을 사용합니다.
- 한투 API 키는 서버 환경변수에만 보관합니다.
