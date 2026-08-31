# Security notes

## Frontend dependency audit

2026-07-29 기준으로 ESLint 10과 flat config로 전환하고 TypeScript·React
플러그인을 호환 버전으로 갱신했습니다. 이 과정에서 기존 ESLint 8 전이
의존성 경고를 제거했으며 `npm audit`의 high severity 집계는 16건에서
2건으로 감소했습니다.

남은 2건은 `react-router-dom`과 그 전이 의존성 `react-router`에 같은
[RSC Mode CSRF 권고](https://github.com/advisories/GHSA-qwww-vcr4-c8h2)가
각각 집계된 것입니다. MOA 프론트엔드는 다음 기능을 사용하지 않습니다.

- React Server Components
- React Router Framework Mode
- Server Actions
- 서버 측 라우트 액션

따라서 현재 클라이언트 전용 `createBrowserRouter` 실행 경로에는 해당 권고가
적용되지 않습니다. npm이 제시하는 자동 수정은 현재 7.18 계열에서 7.11로
내리는 변경이므로 강제 적용하지 않았습니다. 현재 클라이언트 동작을 유지하면서
권고 범위를 벗어나는 호환 버전이 확인되면 갱신합니다.

## Secrets

- 한투·Supabase 키를 프론트엔드 변수에 넣지 않습니다.
- 예외적으로 Supabase `publishable` 키는 브라우저 사용을 전제로 한 공개 키이므로
  `VITE_SUPABASE_PUBLISHABLE_KEY`에 둘 수 있습니다.
- Supabase secret/service-role 키와 기존 JWT shared secret은 절대 프론트엔드에
  두지 않습니다.
- 실제 `.env` 파일은 Git에 커밋하지 않습니다.
- OpenAI API 키는 `backend/.env`의 `OPENAI_API_KEY`에만 두고 브라우저 변수,
  API 응답, 운영 설정 점검 출력에 포함하지 않습니다.
- 주문·토큰·사용자 금융정보를 애플리케이션 로그에 기록하지 않습니다.

## AI strategy explanation

- AI 설명은 사용자가 버튼을 눌렀을 때만 호출하며, 호출 전에 목적·기간·월
  투자금과 규칙 엔진 결과가 OpenAI에 전송된다는 점을 화면에 표시합니다.
- 서버는 클라이언트가 보낸 추천 결과를 신뢰하지 않고 `STRATEGY-2026.07`
  엔진으로 다시 계산한 결과만 모델에 제공합니다.
- 사용자 ID 원문은 보내지 않고 단방향 SHA-256 값만 API 안전 식별자로
  사용합니다. 이메일, access token, 계좌·원장과 목표 금액은 보내지 않습니다.
- 모델 출력은 JSON Schema로 제한하고 실제 규칙 근거 코드만 인용하도록
  재검증합니다. 비중·금액·세율 계산과 최종 투자 결정은 계속 결정적 엔진과
  사용자에게 남습니다.

## Authentication and account isolation

- 운영 백엔드는 `AUTH_MODE=supabase`가 아니면 시작하지 않습니다.
- Bearer token의 payload를 신뢰하거나 단순 디코딩하지 않고 Supabase Auth
  `get_user(jwt)` 호출로 유효성을 검증합니다.
- 클라이언트는 모의투자 API에 `account_id`를 지정할 수 없습니다.
- 서버가 검증된 사용자 ID로 계좌를 결정하고 주문·포지션·현금 원장을 제한합니다.
- 프론트엔드는 로그인 사용자 변경 및 로그아웃 때 서버 상태 캐시를 비웁니다.
