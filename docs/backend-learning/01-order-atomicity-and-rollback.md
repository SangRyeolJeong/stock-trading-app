# 01. 주문 체결의 원자성과 롤백

## 확인하려는 내용

모의 주문 체결은 다음 DB 변경으로 구성된다.

```text
종목과 주문 저장
→ 주문 가능 자원 검증
→ 포지션 변경
→ 체결 저장
→ 매매대금 원장 저장
→ 수수료 원장 저장
→ 포트폴리오 스냅샷 저장
```

이 중 하나라도 예상하지 못한 예외로 완료되지 않으면 전체 작업이 없었던 것처럼
되돌아가야 한다. 반대로 현금이나 보유 수량 부족처럼 예상된 결과는 대기 주문을
`rejected`로 남겨 사용자에게 최종 상태를 알려야 한다.

## 트랜잭션 경계

시세 조회는 DB 트랜잭션 밖에서 수행한다. 시세가 준비된 뒤 공개 서비스 메서드가
`async with session.begin()`으로 하나의 트랜잭션을 시작한다. 내부 저장 단계는
각자의 책임만 수행하며 `commit()`하지 않는다.

SQLAlchemy에서 `flush()`는 세션에 쌓인 변경을 SQL로 DB에 전달하지만 트랜잭션을
확정하지 않는다. 이후 예외가 발생하면 `session.begin()` 컨텍스트가 롤백하고,
이미 flush된 INSERT와 UPDATE도 함께 취소된다. PostgreSQL도 트랜잭션에 묶인 여러
단계를 all-or-nothing 작업으로 처리한다.

상세 선택과 트레이드오프는
[ADR 0001](../adr/0001-paper-order-transaction-boundary.md)에 기록했다.

## 장애 주입 방법

운영 환경변수나 장애용 API는 추가하지 않았다. 테스트가 각 내부 메서드를
monkeypatch하여 다음 지점에 `InjectedSettlementFailure`를 발생시킨다.

| 장애 지점 | 예외 직전 DB에 전달된 변경 |
| --- | --- |
| 주문 생성 직후 | 신규 종목, 주문 |
| 포지션 변경 직후 | 신규 종목, 주문, 포지션 |
| 체결 저장 직후 | 위 항목과 체결 |
| 매매대금 원장 직후 | 위 항목과 매매대금 원장 |
| 수수료 원장 직후 | 위 항목과 두 원장 행 |
| 스냅샷 저장 직전 | 스냅샷을 제외한 모든 체결 데이터 |

첫 다섯 지점은 원래 단계 실행 후 테스트에서 명시적으로 `flush()`한 다음 예외를
발생시킨다. 따라서 단순히 Python 메모리의 ORM 객체만 버려지는지 보는 것이 아니라
DB에 SQL이 전달된 뒤에도 커밋 전 변경이 취소되는지 확인한다.

## 검증하는 상태

각 장애 전후에 다음 상태 전체가 같은지 비교한다.

- 주문 수
- 체결 수
- 현금 원장 행 수와 전체 금액 합계
- 통화별 현금 원장 합계
- 포지션 수량, 평균단가와 실현손익
- 포트폴리오 스냅샷 수
- 트랜잭션 안에서 처음 생성된 종목 목록

롤백 확인 후 같은 멱등성 키로 같은 주문을 다시 실행한다. 재시도가 정상 체결되고
주문 하나, 체결 하나, 매매대금·수수료 원장 두 행과 스냅샷 하나만 생기는지
확인한다.

별도 테스트는 대기 지정가 주문을 만든 뒤 계좌 현금을 줄여 체결 시점에 현금이
부족하도록 한다. 이 경우 시스템 예외처럼 전체 요청을 실패시키지 않고 주문을
`rejected`로 커밋하며, 체결·포지션·체결 원장·스냅샷은 만들지 않는다.

## 실행 방법과 결과

```bash
cd backend
.venv/bin/python -m pytest tests/test_paper_order_atomicity.py
```

2026-08-12 실행 결과:

```text
7 passed
```

## 이 테스트가 증명하지 않는 것

현재 장애 주입 테스트는 SQLite에서 실행한다. 다음 내용은 증명하지 않는다.

- PostgreSQL `SELECT ... FOR UPDATE`의 실제 대기와 잠금 순서
- 동시에 실행되는 독립 트랜잭션 사이의 초과 지출·초과 매도 방지
- 체결과 취소의 경쟁 결과
- DB 프로세스나 운영체제 강제 종료 후의 WAL 내구성
- 외부 증권사 API처럼 DB 롤백 범위 밖에 있는 작업

행 잠금과 동시성은 Alembic으로 만든 PostgreSQL 스키마와 서로 다른
`AsyncSession`을 사용하는 다음 단계 통합 테스트에서 검증한다.

## 공식 문서

- [SQLAlchemy: begin/commit/rollback 블록](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block)
- [SQLAlchemy: flushing](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#flushing)
- [PostgreSQL: Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
