# ADR 0004: 모의 원장 대사와 단계적 append-only 정책

- 상태: 채택
- 결정일: 2026-08-31

## 해결하려는 문제

주문 정산 트랜잭션이 원자적이어도 이후의 결함, 수동 SQL, 잘못된 migration 또는
새 쓰기 경로가 주문·체결·현금 원장·포지션을 서로 다르게 만들 수 있다. 현재
현금은 원장 `amount` 합계로 계산하지만 각 행에는 조회 편의를 위한
`balance_after`도 있으므로 두 표현이 어긋날 수도 있다.

정합성 오류를 자동으로 고쳐 버리면 감사 근거를 더 훼손할 수 있다. 먼저 읽기
전용으로 불일치를 찾고, 기존 원장 행을 수정하지 않는 보정 정책이 필요하다.

## 고려한 선택지

### 애플리케이션 규칙만 사용

원장 모델에 수정·삭제 API를 만들지 않고 코드 리뷰로 insert-only를 유지한다.
구현과 테스트는 단순하지만 migration, 운영 SQL 또는 새 코드 경로를 DB가 막지
못한다.

### PostgreSQL trigger로 UPDATE·DELETE 거부

행 변경 시점에 강제로 차단할 수 있다. 그러나 migration·테스트 정리·비상 복구도
같이 막으므로 우회 역할과 절차가 필요하고, 테이블 소유자와 superuser의 운영
경계를 별도로 설계해야 한다.

### runtime DB 역할에서 UPDATE·DELETE·TRUNCATE 권한 제거

migration 소유자와 애플리케이션 runtime 역할을 분리하면 애플리케이션은
`SELECT`와 `INSERT`만 수행할 수 있다. 운영 경계가 명확하지만 현재 배포는 단일
`DATABASE_URL`을 migration과 API가 공유하므로 자격정보 분리가 선행돼야 한다.

## 최종 선택

현재 단계에서는 다음 방식을 채택한다.

1. `PaperLedgerReconciler`는 하나의 `AsyncSession`에서 계좌 데이터를 읽기만 한다.
2. CLI는 정상 상태에서 0, 불일치에서 1, DB 점검 자체 실패에서 2를 반환한다.
3. 원장 수정·삭제 애플리케이션 기능은 만들지 않는다.
4. 오류를 보정할 때는 기존 행을 바꾸지 않고 별도의 반대 금액 조정 원장을 추가한
   뒤 조정 사유와 승인 근거를 남긴다. 공개 조정 API는 이번 단계에 만들지 않는다.
5. 운영 자격정보를 migration owner와 runtime role로 분리하는 시점에 runtime의
   `UPDATE`, `DELETE`, `TRUNCATE` 권한을 제거한다. 그 전에는 대사 CLI와 코드
   규칙이 탐지·예방 계층이다.

trigger는 당장 추가하지 않는다. 역할 분리 뒤에도 별도 운영 도구가 같은 runtime
역할을 공유하거나 권한 오설정 위험이 확인되면 이 결정을 재검토한다.

## 검사하는 불변식

- `filled` 주문과 체결은 1:1이고 미체결 주문에는 체결이 없다.
- 체결 수량은 주문 수량과 같고 체결 금액은 `가격 × 수량`이다.
- 매수·매도 정산 원장은 각각 `-gross_amount`, `+gross_amount`다.
- 수수료 원장은 `-fee`이며 주문마다 정산·수수료 행이 정확히 하나씩 있다.
- 주문 원장의 계좌·통화는 주문 종목과 일치한다.
- 통화별 최신 `balance_after` 후보 중 하나는 전체 원장 금액 합과 일치한다.
- 종목별 포지션은 매수 체결 합계에서 매도 체결 합계를 뺀 값과 같고 음수가 아니다.

같은 트랜잭션의 여러 행은 DB 기준 시각이 같을 수 있다. 현재 테이블에는 단조
sequence가 없으므로 같은 최신 시각의 행을 모두 후보로 보고 누적 합과 일치하는
행이 하나 이상 있는지 검사한다.

## 결과와 한계

장점:

- 사용자 요청을 처리하지 않고도 전체 계좌 또는 한 계좌의 불일치를 점검한다.
- 문제를 계좌·주문·통화·종목과 안정적인 코드로 출력해 운영 조사에 사용할 수 있다.
- SQLite 장애 주입 테스트가 누락, 잘못된 부호·금액, 상태, 체결 계산과 포지션
  불일치를 검출한다.

한계:

- 대사 시점 이후 새 주문이 커밋되면 보고서는 즉시 오래된 스냅샷이 된다. 일관된
  운영 점검에는 트래픽 제어 또는 PostgreSQL 격리 수준 정책이 추가로 필요하다.
- `balance_after`의 모든 중간 순서는 단조 sequence가 없어 완전히 재구성할 수 없다.
- 평균단가, 실현손익과 포트폴리오 스냅샷 금액은 이번 대사 범위에 포함하지 않았다.
- DB 권한 기반 append-only 강제는 migration/runtime 역할 분리 전까지 남은 운영
  작업이다.
- 자동 보정은 의도적으로 제공하지 않는다.

## 근거

- [SQLAlchemy 2.0: AsyncIO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL 17: Privileges](https://www.postgresql.org/docs/17/ddl-priv.html)
- [PostgreSQL 17: Trigger Behavior](https://www.postgresql.org/docs/17/trigger-definition.html)
