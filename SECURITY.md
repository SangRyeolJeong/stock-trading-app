# Security notes

## Frontend dependency audit

2026-07-25 기준으로 Vite, PostCSS, React Router를 최신 호환 버전으로
업데이트했습니다.

`npm audit --omit=dev`에는 React Router의 RSC Mode 서버 액션에 관한 권고가
남아 있습니다. MOA 프론트엔드는 다음 기능을 사용하지 않습니다.

- React Server Components
- React Router Framework Mode
- Server Actions
- 서버 측 라우트 액션

따라서 현재 클라이언트 전용 `createBrowserRouter` 실행 경로에는 해당 권고가
적용되지 않습니다. 수정 버전이 배포되면 최신 버전으로 갱신합니다.

개발 의존성의 잔여 경고는 레거시 ESLint 8 전이 의존성에서 발생합니다.
ESLint 메이저 업그레이드와 flat config 전환 작업에서 제거할 예정입니다.

## Secrets

- 한투·Supabase 키를 프론트엔드 변수에 넣지 않습니다.
- 실제 `.env` 파일은 Git에 커밋하지 않습니다.
- 주문·토큰·사용자 금융정보를 애플리케이션 로그에 기록하지 않습니다.
