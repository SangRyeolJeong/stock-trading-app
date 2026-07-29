# MOA repository instructions

이 파일은 이 저장소에서 작업하는 Codex가 가장 먼저 따라야 할 프로젝트 지침이다.

## 시작할 때

1. `HANDOFF.md`, `README.md`, `backend/README.md`, `SECURITY.md`를 읽는다.
2. `git status -sb`, `git log --oneline -5`로 현재 브랜치와 변경 사항을 확인한다.
3. 기존 사용자 변경 사항과 `backend/.env`를 보존한다.
4. 작업 전에 `HANDOFF.md`의 현재 상태와 다음 우선순위가 실제 코드와 일치하는지 확인한다.

## 현재 개발 환경

- 이 PC의 기준 작업 복제본은 `/home/user/code/stock-trading-app`이다.
- VS Code는 `WSL: Ubuntu` 원격 창에서 사용한다.
- `/mnt/d/programming`은 마이그레이션 전 보존본이다. 사용자가 명시하지 않는 한 그곳에서 개발하거나 삭제하지 않는다.
- 백엔드는 `backend/.venv`의 Linux CPython 3.12를 사용한다.
- 프론트엔드는 WSL의 Node.js와 `frontend/node_modules`를 사용한다.
- `.venv-win`, Windows Python/Node, `/mnt/d`의 의존성 폴더를 섞어 쓰지 않는다.

## 필수 검증

백엔드 변경 후:

```bash
cd backend
.venv/bin/python -m pytest
.venv/bin/python -m ruff check app tests
```

프론트엔드 변경 후:

```bash
cd frontend
npm test
npm run build
npm run lint
```

작업을 마치기 전:

```bash
git status -sb
```

관련 영역의 검증이 실패한 상태를 완료로 보고하지 않는다.

## 프로젝트 원칙

- 금융·세금 계산은 버전이 있는 결정적 규칙 엔진에서 수행한다.
- AI는 근거 검색과 설명을 담당하며 세율, 수익률, ETF 보수 같은 값을 임의 생성하지 않는다.
- 실제 시세, 모의 주문, 실전 주문의 경계를 분리한다.
- 금액과 수량은 `float` 대신 `Decimal`/DB `NUMERIC`을 사용한다.
- 주문 멱등성과 원장 불변식을 유지한다.
- KIS, Supabase 등 비밀값은 서버 환경변수에만 두고 출력하거나 커밋하지 않는다.
- `backend/.env`, 가상환경, `node_modules`, 빌드 결과와 테스트 캐시는 커밋하지 않는다.
- 의존성 경고를 고칠 때 `npm audit fix --force`처럼 호환성을 깨뜨릴 수 있는 명령을 근거 없이 실행하지 않는다.
- 삭제나 대규모 구조 변경 전에는 사용 여부와 Git 상태를 먼저 확인한다.

## 문서 유지

환경, 완료 범위, 주요 결정 또는 다음 우선순위가 바뀌면 같은 작업에서
`HANDOFF.md`도 갱신한다. 명령이나 경로가 달라지면 README도 함께 고친다.
