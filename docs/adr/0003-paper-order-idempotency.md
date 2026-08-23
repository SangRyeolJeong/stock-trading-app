# ADR 0003: 모의 주문의 요청 fingerprint와 이중 멱등성 확인

- 상태: 채택
- 결정일: 2026-08-23

## 해결하려는 문제

주문 트랜잭션이 커밋된 뒤 HTTP 응답이 유실되면 클라이언트는 같은 주문을 다시
보낸다. 기존 `(account_id, idempotency_key)` 유일 제약은 중복 행을 막지만 다음
두 문제에는 충분하지 않다.

- 기존 주문을 찾기 전에 시세를 조회하면 시세 서비스 장애 때문에 이미 끝난 주문의
  재시도도 실패한다.
- 같은 멱등성 키를 다른 주문 내용에 재사용했는지 안정적으로 판별할 저장값이 없다.

또한 시세 조회 전 기존 주문을 확인하는 것만으로는 충분하지 않다. 첫 조회와 주문
저장 사이에 다른 요청이 같은 키로 커밋할 수 있기 때문이다.

## 고려한 선택지

### 멱등성 키만 비교

구현은 단순하지만 같은 키를 다른 수량이나 종목에 잘못 재사용해도 기존 응답을
반환한다. 클라이언트 오류를 숨기므로 선택하지 않았다.

### 원본 요청 JSON 전체 저장

디버깅에는 유리하지만 JSON 표현 순서, 공백과 소수 표기처럼 의미가 같은 표현을
별도로 정규화해야 한다. 주문 테이블에 중복 데이터를 더 많이 저장하기도 한다.

### 정규화한 주문 내용의 fingerprint 저장

서버가 받아들인 주문 의미를 고정된 표현으로 직렬화하고 SHA-256 digest를 저장한다.
멱등성 키는 주문을 찾는 좌표이고 fingerprint는 같은 요청인지 확인하는 값이 된다.

## 최종 선택

버전 1 fingerprint는 다음 필드로 만든다.

```text
version, symbol, side, order_type, quantity, limit_price
```

- Pydantic 검증 후의 대문자 종목 코드를 사용한다.
- 수량과 지정가는 DB `NUMERIC(28, 8)` 정밀도와 같은 소수점 8자리로 정규화한다.
- 키 순서를 고정한 compact JSON을 UTF-8로 인코딩해 SHA-256을 계산한다.
- `idempotency_key` 자체는 fingerprint에 넣지 않는다. 키가 달라도 주문 내용의
  fingerprint 정의는 같아야 하기 때문이다.
- `request_fingerprint`는 `VARCHAR(64) NOT NULL`로 저장한다.
- 기존 주문은 마이그레이션에서 저장된 정규화 필드로 version 1 fingerprint를
  backfill한 뒤 `NOT NULL`을 적용한다.

주문 API의 확인 순서는 다음과 같다.

```text
기존 계좌·키 조회
├─ 같은 fingerprint: 저장된 주문 반환, 시세 호출 없음
├─ 다른 fingerprint: 409 Conflict, 시세 호출 없음
└─ 없음: 외부 시세 조회
          → 주문 트랜잭션 시작
          → 계좌 행 잠금
          → 계좌·키·fingerprint 재확인
          → 주문·체결·원장 저장
```

첫 조회는 완료된 요청의 재시도를 외부 시세 장애에서 분리하는 최적화다. 계좌 잠금
뒤의 두 번째 조회가 경쟁 요청을 직렬화하며, 기존 `(account_id, idempotency_key)`
유일 제약은 애플리케이션 규약이 누락되더라도 중복 저장을 거부하는 최종 방어선으로
유지한다.

## 결과와 한계

장점:

- 응답 유실 후 재시도는 시세 서비스 상태와 무관하게 저장된 결과를 받는다.
- 같은 키와 다른 요청은 일관되게 `409 Conflict`가 된다.
- 같은 키의 동시 요청도 주문·체결·원장 효과를 한 번만 만든다.
- 실패한 트랜잭션은 키나 fingerprint 행을 남기지 않으므로 같은 키를 재사용할 수
  있다.

한계:

- 신규 주문은 여전히 정상 시세가 필요하다.
- fingerprint는 요청 불일치 검사용이지 인증값이나 보안 서명이 아니다.
- fingerprint 필드를 바꾸면 새 버전을 정의하고 이전 버전의 비교·이관 정책을 함께
  설계해야 한다.
- 현재 backfill은 모든 기존 주문을 한 migration에서 처리한다. 주문량이 커지면
  nullable 추가, 배치 backfill, 검증, `NOT NULL` 적용을 분리해야 한다.
- 비관적 계좌 잠금을 우회하는 새 쓰기 경로는 유일 제약 오류를 도메인 충돌로
  변환하는 처리까지 별도로 갖춰야 한다.

## 근거

- [PostgreSQL 17: Unique Constraints](https://www.postgresql.org/docs/17/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS)
- [SQLAlchemy 2.0: Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Python: hashlib](https://docs.python.org/3/library/hashlib.html)
