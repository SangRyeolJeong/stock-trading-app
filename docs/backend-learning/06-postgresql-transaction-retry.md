# 06. 교착 상태와 트랜잭션 재시도

## 오류가 아니라 트랜잭션을 재시도한다

교착 상태나 직렬화 실패가 나면 실패한 SQL 한 문장만 다시 실행해서는 안 된다.
그 문장을 결정한 앞선 조회 결과도 더는 유효하지 않을 수 있기 때문이다. 주문
서비스의 decorator는 `session.begin()`을 포함한 공개 쓰기 메서드 전체를 다시
호출한다. 컨텍스트 매니저가 실패한 시도의 rollback을 끝낸 뒤 다음 시도가 시작된다.

선택한 범위와 트레이드오프는
[ADR 0006](../adr/0006-postgresql-transaction-retry.md)에 기록했다.

## 분류 정책

| 결과 | SQLSTATE / 예외 | 처리 |
| --- | --- | --- |
| 교착 상태 | `40P01` | 전체 트랜잭션 재시도 |
| 직렬화 실패 | `40001` | 전체 트랜잭션 재시도 |
| 연결 단절 | `08...` | 즉시 실패, 결과 불확실성 조사 |
| 현금·수량 부족 | 도메인 예외 | 즉시 응답 |
| 멱등성 충돌 | 도메인 예외 | 즉시 409 응답 |
| 입력 오류 | Pydantic/FastAPI 검증 | 트랜잭션 진입 전 422 응답 |

메시지 문자열은 서버 버전과 상황에 따라 달라질 수 있으므로 분류에 사용하지 않는다.
SQLAlchemy `DBAPIError.orig`의 `sqlstate` 또는 호환 `pgcode`만 확인한다.

## 상한과 full jitter

기본 정책은 최초 시도를 포함한 최대 3회다. 첫 실패 후 지연 상한은 10ms, 다음은
20ms이며 최대 250ms를 넘지 않는다. 실제 대기값은 매번 `0..상한`에서 무작위로
선택한다. 낮은 지연은 사용자 주문 응답을 과도하게 늦추지 않으면서 동시에 깨어난
트랜잭션들이 즉시 다시 충돌할 가능성을 낮춘다.

재시도 횟수를 늘리면 성공률만 좋아지는 것이 아니라 DB가 과부하일 때 요청량을
증폭할 수 있다. 따라서 환경변수의 최대값을 제한하고 최종 소진은 원래 DB 예외로
반환한다.

## 관측 정보

각 재시도 로그에는 작업명, 분류된 사유, 현재 시도, 최대 시도와 선택한 지연이
별도 필드로 들어간다. 최종 소진 로그에는 같은 식별 필드가 들어간다. 메트릭은
사유별 `retries_total`과 `exhausted_total` 카운터다.

카운터는 현재 프로세스 메모리에만 있으므로 운영 집계의 완성형은 아니다. 여러
인스턴스의 합산과 재시작 보존이 필요해지면 Prometheus/OpenTelemetry exporter를
연결해야 한다. 로그에는 주문 원문, 사용자 ID, 계좌 ID나 DB 연결 정보가 들어가지
않는다.

## 자동화 테스트가 증명하는 것

- 두 재시도 SQLSTATE는 실패한 횟수만큼 카운터·로그를 남기고 성공할 수 있다.
- exponential ceiling과 full jitter로 계산한 대기값을 사용한다.
- 최대 시도 뒤 원래 예외를 다시 발생시키고 소진 카운터를 남긴다.
- 연결 오류와 비즈니스 오류는 한 번만 실행한다.
- 주문 쓰기 메서드는 첫 트랜잭션 실패를 rollback한 뒤 같은 세션에서 성공한다.
- PostgreSQL 전용 테스트는 두 계좌 행을 반대 순서로 잠가 실제 교착을 만들고,
  중단된 한 작업만 전체 트랜잭션으로 다시 실행되는지 확인한다.

## 공식 문서

- [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL: Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
- [SQLAlchemy 2.0: Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
