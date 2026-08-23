# 03. 멱등성과 안전한 주문 재시도

## 장애는 성공 응답 뒤에도 생긴다

서버가 주문, 체결과 원장을 모두 커밋해도 응답을 보내는 순간 연결이 끊길 수 있다.
클라이언트 관점에서는 성공 여부를 알 수 없으므로 동일 요청을 재전송해야 한다.
이때 서버가 두 번째 주문을 만들면 재시도 자체가 금융 효과를 중복시킨다.

멱등성은 같은 요청을 여러 번 처리해도 한 번 처리한 것과 같은 결과를 만드는
성질이다. 이 구현에서는 계좌와 클라이언트가 보낸 `idempotency_key`로 기존 주문을
찾고, 정규화한 요청 fingerprint로 정말 같은 주문인지 확인한다.

상세 결정과 트레이드오프는
[ADR 0003](../adr/0003-paper-order-idempotency.md)에 기록했다.

## fingerprint가 필요한 이유

키만 비교하면 다음 두 요청을 구분하지 못한다.

```json
{"symbol":"QQQM","side":"buy","order_type":"market","quantity":1,"idempotency_key":"order-1"}
{"symbol":"QQQM","side":"buy","order_type":"market","quantity":2,"idempotency_key":"order-1"}
```

version 1 fingerprint는 종목, 매수·매도, 주문 유형, 수량과 지정가를 정규화한 JSON의
SHA-256 digest다. 소수는 DB 정밀도와 동일한 8자리로 맞추므로 `1`, `1.0`과
`1.000000000`은 같은 주문 의미로 본다. 같은 키에서 digest가 다르면 API는
`409 Conflict`를 반환한다.

SHA-256을 쓴다고 요청이 비밀이 되거나 인증되는 것은 아니다. 여기서는 가변 길이
요청 내용을 고정 길이 비교값으로 만드는 용도일 뿐이다.

## 왜 두 번 조회하는가

첫 조회는 외부 시세 호출보다 먼저 수행한다.

- 같은 요청이 이미 있으면 저장된 응답을 즉시 반환한다.
- 같은 키의 다른 요청이면 즉시 충돌을 반환한다.
- 따라서 완료된 주문의 재시도는 시세 서비스가 중단돼도 성공한다.

하지만 첫 조회 직후 두 요청이 모두 "없음"을 볼 수 있다. 그래서 시세 조회 후 주문
트랜잭션 안에서 계좌 행을 잠그고 다시 조회한다. 앞선 요청이 커밋하면 기다리던
요청은 잠금 획득 후 그 주문을 보게 된다. DB의 계좌·키 복합 유일 제약도 그대로
남겨 중복 행을 마지막으로 차단한다.

## 마이그레이션

`20260823_0004` migration은 다음 순서로 기존 데이터를 보존한다.

```text
nullable fingerprint 열 추가
→ 기존 주문의 저장 필드로 fingerprint backfill
→ fingerprint를 NOT NULL로 변경
```

애플리케이션 모델은 처음부터 non-null 필드로 다루므로 배포 시에는 migration을
먼저 적용해야 한다. 현재 데이터 규모에서는 한 번에 backfill하지만 대규모 운영
테이블에서는 배치 migration으로 나누는 편이 안전하다.

## 자동화 테스트가 증명하는 것

- 같은 요청의 순차 재시도는 같은 주문 ID를 반환하고 주문·체결·원장을 늘리지 않는다.
- 완료된 주문 재시도와 같은 키의 충돌은 시세 함수를 호출하지 않는다.
- 같은 키의 다른 수량은 `409 Conflict`가 된다.
- PostgreSQL에서 동일 키 요청 두 건을 경쟁시키면 주문과 체결이 각각 하나만 남는다.
- PostgreSQL에서 동일 키·다른 수량을 경쟁시키면 한 건만 성공하고 다른 한 건은
  멱등성 충돌이 된다.
- 정산 중 예외로 전체 롤백된 키는 다시 사용할 수 있다.
- 기존 행 backfill 결과와 애플리케이션 fingerprint가 같고 새 열은 `NOT NULL`이다.

로컬 SQLite 테스트는 API 순서, fingerprint와 원자성을 검증한다. 실제 행 잠금과
동시성은 Alembic head를 적용한 PostgreSQL 전용 테스트와 CI에서 검증한다.

## 공식 문서

- [PostgreSQL 17: Unique Constraints](https://www.postgresql.org/docs/17/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS)
- [SQLAlchemy 2.0: Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Python: hashlib](https://docs.python.org/3/library/hashlib.html)
