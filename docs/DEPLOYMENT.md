# MOA deployment guide

## 권장 구성

```text
브라우저
├── HTTPS → 정적 프론트엔드(Nginx/CDN)
├── HTTPS/WSS → FastAPI
└── HTTPS → Supabase Auth

FastAPI
├── PostgreSQL
├── Supabase Auth token verification
└── KIS REST API(선택)
```

Redis는 현재 코드에서 사용하지 않는다. 프로세스 간 시세 캐시나 작업 큐를
실제로 도입할 때 별도 설계와 함께 추가한다.

## 백엔드 필수 환경변수

```text
APP_ENV=production
AUTH_MODE=supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<database>
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=5
DATABASE_POOL_TIMEOUT_SECONDS=10
DATABASE_POOL_RECYCLE_SECONDS=1800
DATABASE_CONNECT_TIMEOUT_SECONDS=10
DATABASE_COMMAND_TIMEOUT_SECONDS=30
CORS_ORIGINS=https://<frontend-origin>
MARKET_DATA_PROVIDER=mock
```

실제 KIS 시세를 사용할 때만 `MARKET_DATA_PROVIDER=kis`와 KIS 서버 비밀값을
추가한다. Supabase secret/service-role 키와 KIS 비밀값은 배포 플랫폼의 비밀
저장소에 두고 이미지 build argument나 프론트엔드 변수로 전달하지 않는다.

관리형 PostgreSQL이 TLS를 요구하면 공급자 문서에 맞는 asyncpg 연결 옵션을
사용한다. 애플리케이션은 stale connection pre-ping, LIFO 풀, 30분 연결 재생성,
연결/쿼리 timeout을 기본 적용한다. DB의 최대 연결 수에서 migration·관리·상태
확인용 여유를 제외한 뒤, 모든 인스턴스의
`DATABASE_POOL_SIZE + DATABASE_MAX_OVERFLOW` 합계가 그보다 작게 설정되어야
한다. 외부 transaction pooler를 사용할 때는 공급자의 prepared statement
지원 방식도 함께 확인한다.

## 프론트엔드 build argument

```text
VITE_API_BASE_URL=https://<api-origin>
VITE_AUTH_MODE=supabase
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

`VITE_*` 값은 빌드 결과에 포함된다. publishable key 외에는 비밀값을 넣지
않는다. Supabase Dashboard의 Site URL과 허용 Redirect URL에도 실제 프론트엔드
주소를 등록한다.

## 배포 순서

1. PostgreSQL 백업과 연결 상태를 확인한다.
2. 새 백엔드 이미지로 `python -m alembic upgrade head`를 단일 migration
   job에서 실행한다.
3. `/health`와 `/ready`가 각각 200인지 확인한다.
4. 백엔드를 순차 배포한다.
5. 실제 API/Supabase 주소로 프론트엔드를 빌드하고 배포한다.
6. 신규 사용자 로그인, 사용자 A/B 원장 격리, 주문 멱등성, 로그아웃 후 캐시
   초기화를 스모크 테스트한다.

백엔드 Dockerfile도 시작 시 마이그레이션을 적용해 단일 인스턴스 배포에는
편리하지만, 여러 인스턴스를 동시에 시작하는 운영 환경에서는 배포 단계의 단일
migration job으로 분리하는 편이 안전하다.

## 상태 확인과 운영

- `/health`: 프로세스와 설정 로드 상태
- `/ready`: PostgreSQL 연결을 포함한 요청 처리 준비 상태
- 로그에 Authorization header, access token, 주문 원문 또는 사용자 금융정보를
  기록하지 않는다.
- PostgreSQL 자동 백업, point-in-time recovery, 복구 리허설을 운영 요구사항에
  맞게 설정한다.
- 배포 전후 현재 `67`개 백엔드 테스트, Ruff, `7`개 프론트 테스트,
  프론트 빌드와 ESLint, PostgreSQL 17 마이그레이션·readiness 스모크,
  컨테이너 이미지 빌드를 통과해야 한다.

## 출시 전 제품 결정

다음 항목은 인프라 코드만으로 결정하지 않고 개인정보·금융 데이터 정책과 함께
확정해야 한다.

- 계정 삭제 시 모의투자 원장 즉시 삭제 또는 법정·운영 보존 기간
- 사용자 설정을 서버에 동기화할 범위
- 관리자 접근 권한과 감사 로그
- 장애 시 주문 API 쓰기 차단 및 복구 절차
- KIS 호출 제한을 넘는 규모에서의 공유 캐시와 rate limiter
