# AI 전략 설명 경계

MOA의 첫 생성형 AI 기능은 전략을 새로 계산하지 않고 `STRATEGY-2026.07` 규칙
엔진의 결과를 쉬운 한국어로 설명한다. 계산과 생성의 경계는 다음과 같다.

```text
검증된 StrategyRequest
→ 서버의 결정적 전략 추천 계산
→ 추천 결과와 reason code만 OpenAI Responses API에 전달
→ JSON Schema 구조화 출력
→ reason code 허용 목록 재검증
→ 설명·주의점 표시
```

## 안전 원칙

- 호출은 사용자의 `AI 설명 생성` 버튼 이후에만 수행한다.
- OpenAI API 키는 백엔드 환경변수에만 둔다.
- 사용자의 이메일과 ID 원문, access token, 계좌·원장 데이터는 보내지 않는다.
- 안전 식별자는 사용자 ID의 SHA-256 값으로 만들며 원문을 복원할 수 없게 한다.
- 모델은 비중, 금액, 수익률, 세율과 상품을 추가하거나 바꾸지 않는다.
- 모든 설명 항목은 규칙 엔진이 반환한 `reason_codes` 중 하나 이상을 인용한다.
- 모델 응답이 미완료이거나 스키마·근거 검증에 실패하면 설명 전체를 폐기한다.
- 규칙 추천 API는 AI 설정이나 공급자 장애와 무관하게 계속 동작한다.

구조화 출력은 OpenAI의 공식
[Structured Outputs 문서](https://developers.openai.com/api/docs/guides/structured-outputs)를
기준으로 Responses API의 strict JSON Schema 형식을 사용한다.

## 설정과 검증

기본값은 `AI_PROVIDER=disabled`다. 실제 호출에는 다음 서버 환경변수가 필요하다.

```text
AI_PROVIDER=openai
OPENAI_API_KEY=<server-only secret>
OPENAI_MODEL=gpt-5.6
AI_REQUEST_TIMEOUT_SECONDS=20
```

자동화 테스트는 실제 외부 API를 호출하지 않고 `httpx.MockTransport`로 요청
본문, 비밀 헤더, 구조화 출력 파싱, 알 수 없는 근거 코드와 미완료 응답 거부를
검증한다. 실제 모델 품질과 계정별 한도·비용은 배포 환경에서 별도로 확인한다.
