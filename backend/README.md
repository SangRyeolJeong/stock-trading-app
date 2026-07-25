# MOA API

비동기 시세 스트림, 모의 주문, 절세·전략 계산을 제공하는 FastAPI 백엔드입니다.
한투 API 키가 없을 때는 프론트엔드 개발용 데모 데이터로 동작합니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API 문서는 서버 실행 후 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 설계 원칙

- 금융·세금 계산은 버전이 기록되는 규칙 엔진에서 결정적으로 수행합니다.
- AI는 근거 검색과 설명을 담당하고 계산 결과를 임의로 만들지 않습니다.
- 실전 주문과 모의 주문의 모델·라우터·자산 원장은 분리합니다.
- 한투 REST 토큰은 Redis에 캐시하고 실시간 시세는 서버 WebSocket으로 재배포합니다.
