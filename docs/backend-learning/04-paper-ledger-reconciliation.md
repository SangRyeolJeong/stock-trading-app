# 04. 원장 불변식과 읽기 전용 대사

## 트랜잭션만으로 충분하지 않은 이유

원자적 주문 정산은 한 요청 안에서 일부 데이터만 커밋되는 일을 막는다. 하지만
나중의 코드 결함, 수동 SQL 또는 migration이 이미 저장된 주문·체결·원장·포지션을
서로 다르게 만들 가능성까지 없애지는 않는다. 대사는 서로 독립적으로 계산할 수
있는 기록을 다시 비교해 이런 차이를 찾는 과정이다.

상세 선택지와 append-only 결정은
[ADR 0004](../adr/0004-paper-ledger-reconciliation.md)에 기록했다.

## 대사 흐름

```text
계좌 목록
├─ 주문 + 종목 통화
├─ 체결
├─ 현금 원장
└─ 포지션
   → 주문별 체결·원장 검사
   → 통화별 잔액 검사
   → 종목별 체결 누적과 포지션 검사
   → 문제 코드가 있는 읽기 전용 보고서
```

`PaperLedgerReconciler`는 ORM 객체를 변경하거나 트랜잭션을 커밋하지 않는다. 전체
계좌를 점검하거나 `account_id` 하나로 범위를 제한할 수 있다.

## 실행과 종료 코드

```bash
cd backend
.venv/bin/python -m app.cli.reconcile_paper_ledger
.venv/bin/python -m app.cli.reconcile_paper_ledger --account-id demo-account
```

- `0`: 검사한 모든 계좌가 일관됨
- `1`: 불일치 또는 요청한 계좌가 없음
- `2`: DB 연결이나 대사 쿼리 자체가 실패함

내부 DB 오류에는 연결 문자열이나 자격정보가 들어갈 수 있으므로 CLI는 원문 예외를
출력하지 않는다. 불일치에는 안정적인 문제 코드와 계좌, 필요한 경우 주문·통화·
종목 범위를 출력한다.

## `balance_after` 검사의 한계

현금의 현재값은 모든 `amount` 합계로 다시 계산할 수 있다. 반면
`balance_after`는 각 쓰기 시점의 캐시다. 한 트랜잭션에서 정산과 수수료 행의 DB
시각이 같을 수 있고 UUID는 저장 순서를 표현하지 않으므로 모든 중간 잔액을 완전히
재생할 수는 없다.

현재 대사기는 통화별 가장 최신 시각의 행들을 후보로 모아 그중 하나가 전체
`amount` 합계와 일치하는지 검사한다. 모든 중간 순서를 감사해야 한다면 원장에
계좌·통화별 단조 sequence를 추가하는 migration이 필요하다.

## 자동화 테스트가 증명하는 것

- 정상 매수·매도 뒤 주문 2건, 체결 2건, 초기 입금 포함 원장 6건과 포지션 1건이
  문제 없이 대사된다.
- 체결이 있는데 주문 상태를 미체결로 바꾸면 탐지한다.
- 수수료 원장을 삭제하거나 매매대금 원장 금액을 바꾸면 탐지한다.
- 체결 금액과 포지션 수량을 손상시키면 각각 계산 불일치를 탐지한다.
- 없는 계좌를 명시하면 성공으로 오인하지 않는다.
- CLI는 문제 범위와 종료 코드를 제공하고 DB 예외의 비밀 문자열을 숨긴다.

손상 데이터는 테스트에서만 직접 UPDATE·DELETE한다. 운영 보정은 기존 원장을
수정하지 않고 반대 금액 조정 원장을 추가하는 방식이어야 하며, 공개 조정 기능은
승인·사유·감사 요구사항이 정해질 때 별도로 구현한다.

## 공식 문서

- [SQLAlchemy 2.0: AsyncIO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL 17: Privileges](https://www.postgresql.org/docs/17/ddl-priv.html)
- [PostgreSQL 17: Trigger Behavior](https://www.postgresql.org/docs/17/trigger-definition.html)
