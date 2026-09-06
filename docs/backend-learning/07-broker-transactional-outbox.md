# 07. 실제 증권사 주문과 Transactional Outbox

## DB rollback으로 외부 주문을 취소할 수 없는 이유

DB 트랜잭션은 같은 DB 안의 변경만 원자적으로 되돌린다. 증권사 API가 주문을
접수한 뒤 로컬 commit이 실패해도 DB rollback은 외부 접수를 취소하지 않는다.
따라서 로컬 주문 저장과 외부 호출을 직접 이어 붙이지 않고, 전송 의도를 DB에
함께 저장하는 outbox가 필요하다.

설계 선택과 운영 한계는
[ADR 0007](../adr/0007-broker-transactional-outbox.md)에 기록했다.

## 처리 흐름

```text
주문 명령
→ DB transaction: broker_order(pending_submission) + submit outbox
→ worker: due outbox FOR UPDATE SKIP LOCKED
→ Fake/실제 gateway에 client_order_id와 주문 전송
   ├─ 응답 성공: submitted + outbox processed
   ├─ 응답 유실: client_order_id 조회 → 발견 시 submitted
   └─ 미발견/일시 실패: backoff → 상한 뒤 reconciliation_required
```

취소는 `submitted → cancel_pending`과 취소 outbox를 원자적으로 만든다. 외부 취소
실패 시 로컬 상태를 이전으로 rollback해 성공처럼 보이지 않고, 조회로 취소를
확인하거나 다시 시도한다.

## 저장하는 정보

브로커 주문은 client order ID, broker order ID, 종목·방향·유형·수량·지정가,
로컬 상태와 마지막 오류를 가진다. outbox는 주문 ID, submit/cancel 종류, 처리
상태, 시도 횟수, 다음 시각, 마지막 오류와 처리 시각을 가진다. 비밀값과 인증
토큰은 저장하지 않는다.

같은 계좌의 client order ID는 유일하다. 같은 ID와 같은 명령은 기존 주문을
반환하고, 다른 명령이면 충돌로 거절한다. worker가 DB 커밋 결과를 받지 못하고
다시 실행되더라도 gateway가 같은 client order ID를 조회·재사용해야 한다.

## `SKIP LOCKED`의 의미

여러 worker가 같은 pending 행을 보더라도 먼저 잠근 worker만 처리한다. 다른
worker는 기다리지 않고 잠긴 행을 건너뛴다. PostgreSQL 문서도 일반 조회의 일관된
뷰에는 적합하지 않지만 queue-like table의 다중 consumer 경합 회피에 사용할 수
있다고 설명한다.

SQLite는 실제 행 잠금과 `SKIP LOCKED` 동작을 증명하지 못한다. PostgreSQL 전용
테스트는 첫 gateway 호출을 의도적으로 멈춘 상태에서 두 번째 worker를 실행해
외부 submit 호출이 정확히 한 번인지 확인한다.

## 장애 테스트

- outbox 저장 전 예외가 발생하면 주문과 이벤트가 모두 rollback된다.
- 같은 client order ID 재요청은 주문과 이벤트를 중복 생성하지 않는다.
- 처리된 이벤트를 다시 조회해도 gateway를 재호출하지 않는다.
- 증권사 접수 직후 응답 유실은 client order ID 조회로 복구한다.
- 반복 전송 실패는 상한 뒤 자동 성공 처리하지 않고 대사 필요 상태가 된다.
- 명시적 대사는 나중에 발견된 증권사 주문으로 실패 이벤트를 확정한다.
- 취소 실패는 pending으로 남고 후속 시도에서 확인된 취소만 확정한다.

## 현재 한계

실제 KIS gateway, 공개 실전주문 API, 장기 실행 worker와 운영 알림은 의도적으로
포함하지 않았다. 부분 체결·정정·만료도 아직 모델링하지 않는다. 현재 worker는
네트워크 호출 동안 DB 잠금을 유지하므로 운영 연결 전 timeout과 lease 기반 claim
전환을 검토해야 한다.

## 공식 문서

- [AWS: Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- [PostgreSQL: SELECT](https://www.postgresql.org/docs/current/sql-select.html)
