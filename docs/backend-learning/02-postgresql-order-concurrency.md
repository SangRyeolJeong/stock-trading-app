# 02. PostgreSQL 동시 주문과 행 잠금

## 문제 상황

현금이 주문 한 건분만 있더라도 두 요청이 잠금 없이 같은 잔액을 읽으면 둘 다
매수 가능하다고 판단할 수 있다. 하나의 포지션을 두 요청이 동시에 읽는 매도도
같은 문제가 있다.

- Lost Update는 두 트랜잭션이 같은 값을 읽고 각각 변경한 뒤 한 변경이 다른 변경을
  덮어쓰는 현상이다.
- Write Skew는 각 트랜잭션이 서로 다른 행을 변경하더라도 함께 지켜야 하는 조건을
  같은 과거 스냅샷으로 판단해 전체 불변식을 깨뜨리는 현상이다.

MOA의 현금은 여러 원장 행의 합계이므로 집계 결과 자체를 행 잠금할 수 없다. 대신
모든 동일 계좌 주문이 공유하는 `paper_accounts` 행을 직렬화 지점으로 사용한다.

## 구현한 잠금 규칙

`PaperTradingService._lock_user_account()`가 계좌를 다음 형태로 잠근다.

```sql
SELECT ...
FROM paper_accounts
WHERE id = :account_id AND user_id = :user_id
FOR UPDATE OF paper_accounts;
```

기존 주문을 변경할 때는 계좌 잠금 다음에 대상 주문만 잠근다.

```sql
SELECT ...
FROM paper_orders
WHERE id = :order_id AND account_id = :account_id
FOR UPDATE OF paper_orders;
```

체결 과정에서 포지션이 존재하면 마지막으로 해당 포지션을 잠근다. 신규 주문,
대기 지정가 주문 체결과 취소가 모두 `계좌 → 주문 → 포지션` 순서를 따른다.

취소 응답에 필요한 실행·종목 정보는 주문 행을 잠근 뒤 별도 일반 조회로 가져온다.
이전처럼 `paper_executions` outer join까지 한꺼번에 `FOR UPDATE`하지 않으므로
PostgreSQL의 nullable outer-join 측 잠금 오류를 피하고 잠금 범위도 분명해진다.

상세 선택은 [ADR 0002](../adr/0002-paper-order-locking.md)에 기록했다.

## PostgreSQL 테스트 환경

전용 테스트는 `backend/tests/postgres/`에 분리했다.

- `MOA_TEST_DATABASE=postgresql`과 명시적인 `postgresql+asyncpg://` URL이 모두
  있어야 실행한다.
- 일반 테스트의 `Base.metadata.create_all()` fixture를 PostgreSQL에서는
  실행하지 않는다.
- 테스트 시작 시 `alembic_version`이 현재 head인지 검사한다.
- 각 테스트는 Alembic으로 생성된 테이블을 `TRUNCATE ... CASCADE`하여 격리한다.
- 경쟁 요청마다 독립적인 `AsyncSession`을 생성한다.
- 두 작업이 모두 계좌 잠금 직전까지 도착하는 asyncio 장벽을 사용해 실제 경쟁을
  만든다.
- 테스트 종료 시 엔진 풀을 dispose하여 pytest의 서로 다른 event loop 사이에
  asyncpg 연결이 재사용되지 않게 한다.

CI의 PostgreSQL 17 서비스에서는 다음 순서로 실행한다.

```text
alembic upgrade head
→ pytest tests/postgres
→ deployment preflight
→ API readiness/bootstrap smoke test
```

## 동시성 시나리오와 불변식

### 현금 한 건분으로 동시 매수

두 주문을 동시에 시작한다. 하나만 체결되고 다른 하나는
`InsufficientCashError`로 전체 롤백되어야 한다. 최종 USD 잔액은 음수가 아니며
주문·체결·원장 효과는 한 건만 존재해야 한다.

### 한 포지션으로 동시 매도

한 주를 먼저 매수한 뒤 한 주 매도 두 건을 동시에 시작한다. 하나만 체결되고 다른
하나는 `InsufficientPositionError`가 되어야 한다. 최종 수량은 0이며 음수가 될 수
없다.

### 동일 멱등성 키 동시 주문

동일 요청을 동시에 보내도 두 호출은 같은 주문 ID를 반환해야 한다. 주문과 체결은
각각 하나, 주문에 연결된 매매대금·수수료 원장은 두 행만 존재해야 한다.

### 지정가 주문 체결과 취소 경쟁

같은 대기 주문을 한 세션은 체결하고 다른 세션은 취소한다. 최종 상태는
`filled` 또는 `cancelled` 중 하나뿐이다. 체결이 이기면 취소는 상태 오류가 되고
체결 한 건이 남는다. 취소가 이기면 체결은 no-op이며 체결 행이 없어야 한다.

### 신규 사용자의 첫 계좌 동시 생성

같은 사용자의 최초 계좌 생성을 동시에 실행한다. 두 호출은 같은 계좌를 반환하고
계좌는 하나, KRW와 USD 초기 입금은 통화별로 정확히 한 행만 생성되어야 한다.

각 시나리오 후 공통 검사로 다음을 확인한다.

- 통화별 현금 원장 합계가 음수가 아니다.
- 포지션 수량이 음수가 아니다.
- 모든 `filled` 주문은 정확히 하나의 체결을 가진다.
- `filled`가 아닌 주문은 체결을 가지지 않는다.

## 실행 방법

```bash
cd backend
MOA_TEST_DATABASE=postgresql \
DATABASE_URL=postgresql+asyncpg://<user>:<password>@127.0.0.1:5432/<test_db> \
.venv/bin/python -m pytest tests/postgres -vv
```

테스트 DB에는 먼저 다음 마이그레이션을 적용해야 한다.

```bash
DATABASE_URL=postgresql+asyncpg://<user>:<password>@127.0.0.1:5432/<test_db> \
.venv/bin/python -m alembic upgrade head
```

현재 로컬 WSL 환경에는 PostgreSQL 서버와 Docker가 없어 실제 PostgreSQL 실행은
CI 검증 대상으로 남는다. 로컬 일반 테스트에서는 5개 PostgreSQL 테스트가
명시적으로 skip되며, SQLite 테스트 결과를 행 잠금의 증거로 사용하지 않는다.

## 공식 문서

- [PostgreSQL 17: Explicit Locking](https://www.postgresql.org/docs/17/explicit-locking.html#LOCKING-ROWS)
- [PostgreSQL 17: Read Committed](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-READ-COMMITTED)
- [SQLAlchemy: with_for_update](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.GenerativeSelect.with_for_update)
