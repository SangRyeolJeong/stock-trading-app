# 05. 주문 상태 머신과 감사 이력

## 상태와 이벤트를 함께 저장하는 이유

현재 상태는 빠른 조회를 위한 스냅샷이고 상태 이벤트는 그 상태에 도달한 근거다.
둘 중 하나만 저장하면 조회 성능 또는 감사 가능성을 잃는다. 이 구현은 같은
`session.begin()` 트랜잭션에서 주문 상태 변경과 이벤트 INSERT를 수행해 둘을 함께
커밋하거나 함께 롤백한다.

상세 설계 선택과 한계는 [ADR 0005](../adr/0005-paper-order-state-machine.md)에
기록했다.

## 상태 그래프

```text
생성 ──→ accepted ──→ filled
                  ├─→ cancelled
                  └─→ rejected

filled / cancelled / rejected = 종료 상태
```

`paper_order_state.py`가 유일한 정상 전이 함수를 제공한다. 종료 상태에서의 전이는
`InvalidOrderStateError`로 거절된다. 반복 취소는 전이가 아니라 같은 결과의 안전한
재조회로 처리하므로 취소 이벤트도 한 번만 생긴다.

## 감사 이력

`order_status_events`는 다음을 저장한다.

- 주문별 단조 sequence
- 이전 상태와 새 상태
- 안정적인 변경 이유
- DB 변경 시각

`GET /api/v1/paper/orders/{order_id}/events`는 현재 사용자가 소유한 주문만 sequence
순으로 반환한다. 직접 DB 수정 등으로 현재 주문 상태가 마지막 이벤트와 달라지면
`PaperLedgerReconciler`가 `ORDER_STATUS_EVENT_MISMATCH`로 보고한다.

## DB 방어선과 migration

`paper_orders.status`의 `CHECK`는 정의되지 않은 상태를 거부한다. 이벤트 테이블의
제약은 생성 이벤트가 `NULL → accepted`, 종료 이벤트가 `accepted → 종료 상태`인지
검사하고 `(order_id, sequence)` 중복도 막는다.

기존 데이터에는 과거 사유와 종료 시각이 없으므로 migration은 정확한 사실을
추측하지 않는다. 현재 상태를 재현하는 최소 이벤트를 원래 주문 생성 시각에
`migration_backfill` 사유로 추가한다.

## 자동화 테스트가 증명하는 것

- `accepted`는 세 종료 상태로 전이할 수 있고 종료 상태는 다시 전이할 수 없다.
- 즉시 체결 주문에는 생성과 체결 이벤트가 순서대로 남는다.
- 반복 취소는 성공하지만 이벤트를 중복 생성하지 않는다.
- 현재 상태와 마지막 이벤트가 다르면 대사기가 탐지한다.
- migration은 기존 주문 이력을 역채우고 알 수 없는 주문 상태를 DB에서 거부한다.
- 기존 PostgreSQL 체결·취소 경쟁 테스트는 하나의 종료 결과만 허용한다.

## 현재 한계

현재 그래프는 부분 체결과 주문 정정·만료를 표현하지 않는다. 주문당 sequence를
1과 2로 고정한 이유도 이 단순한 그래프 때문이다. 실제 증권사 연동 전에 외부 제출
상태와 반복 이벤트를 포함하도록 상태 모델과 sequence 할당 방식을 재설계해야 한다.

## 공식 문서

- [SQLAlchemy 2.0: Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [PostgreSQL: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
