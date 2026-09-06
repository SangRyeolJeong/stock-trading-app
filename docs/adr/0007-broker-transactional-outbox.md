# ADR 0007: 브로커 주문 Transactional Outbox와 대사

- 상태: 채택
- 결정일: 2026-09-06

## 해결하려는 문제

로컬 DB 커밋과 외부 증권사 주문 접수는 하나의 원자적 트랜잭션으로 묶을 수 없다.
DB만 성공하면 주문이 전송되지 않고, 증권사 접수 뒤 응답이나 DB 커밋이 실패하면
재전송이 중복 주문을 만들 수 있다. 취소도 로컬 rollback으로 증권사 주문을
되돌릴 수 없다.

## 고려한 선택지

### API 트랜잭션 안에서 증권사 동기 호출

사용자에게 즉시 결과를 주지만 DB 잠금을 네트워크 동안 유지하고, 두 시스템 중
하나만 성공하는 dual-write 문제를 해결하지 못한다.

### 분산 트랜잭션

두 참여자가 prepare/commit을 지원해야 하지만 일반 증권사 REST API는 DB의
2-phase commit 참여자가 아니다.

### Transactional Outbox와 client order ID 대사

로컬 주문과 전송 의도를 같은 DB 트랜잭션에 저장하고 worker가 나중에 전송한다.
중복 가능성은 broker에 전달하는 안정적인 client order ID와 재조회로 처리한다.

## 최종 선택

세 번째 방식을 채택한다.

- `broker_orders`와 `broker_outbox_events`를 같은 트랜잭션에 INSERT한다.
- worker는 due 이벤트를 `FOR UPDATE SKIP LOCKED`로 하나씩 점유한다.
- 제출 응답이 유실되면 재전송 전에 client order ID로 증권사 주문을 조회한다.
- 전송·취소는 최대 3회 시도하고 지수 backoff 뒤에도 불명확하면
  `reconciliation_required`로 격리한다.
- 명시적 대사는 증권사 조회 결과가 있을 때만 로컬 주문과 이벤트를 확정한다.
- 취소는 rollback이 아니라 `cancel_pending` outbox와 확인 조회를 사용하는
  best-effort 보상 작업이다.
- 실제 KIS 주문 API와 공개 실전주문 endpoint는 이번 단계에서 연결하지 않는다.
  `FakeBrokerGateway`로 복구 의미를 먼저 검증한다.

worker는 현재 외부 호출 동안 선택한 outbox 행의 DB 잠금을 유지한다. 구현은
단순하고 중복 worker를 막지만 느린 증권사 응답이 커넥션과 잠금을 오래 점유한다.
트래픽이 늘면 짧은 claim 트랜잭션과 lease/heartbeat 상태로 분리해야 한다.

## 장점과 단점

장점:

- 로컬 주문만 있거나 outbox만 있는 부분 커밋이 생기지 않는다.
- worker 중복 실행과 응답 유실을 명시적으로 테스트할 수 있다.
- 제출과 취소의 미확정 상태를 성공으로 가장하지 않는다.

단점:

- exactly-once 전송을 보장하지 않으며 broker의 client order ID 멱등성과 조회에
  의존한다.
- 프로세스 worker 실행기, 운영 스케줄링, dead-letter 알림은 아직 없다.
- 주문 체결·부분 체결 상태와 기존 모의 원장은 연결하지 않았다.

## 변경이 필요한 조건

KIS 주문 API를 연결하기 전에 client order ID 지원 범위, 조회 지연, 취소 응답과
부분 체결 계약을 검증한다. worker 처리량이 필요하면 claim lease를 도입하고,
실패 이벤트 알림·수동 재처리 권한·감사 로그를 운영 요구사항으로 추가한다.

## 근거

- [AWS: Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- [PostgreSQL: SELECT locking clause](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
