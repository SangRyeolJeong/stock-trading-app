import hashlib
import json

import httpx
import pytest

from app.core.config import Settings
from app.schemas.strategy import StrategyRequest
from app.services.strategy import strategy_service
from app.services.strategy_explanation import (
    OpenAIStrategyExplanationService,
    StrategyExplanationFailed,
)


def strategy_request() -> StrategyRequest:
    return StrategyRequest(
        goal="retirement",
        horizon_years=30,
        monthly_amount_krw=500_000,
        risk_profile="growth",
        liquidity_preference=True,
        fee_sensitivity=True,
        income_preference=False,
        tax_efficiency_priority=True,
    )


def openai_settings() -> Settings:
    return Settings(
        _env_file=None,
        ai_provider="openai",
        openai_api_key="test-openai-key",
        openai_model="gpt-5.6",
        database_url="sqlite+aiosqlite://",
    )


def response_body(evidence_code: str = "GOAL_RETIREMENT") -> dict[str, object]:
    narrative = {
        "overview": "규칙 엔진 결과를 장기 계획 관점에서 풀어 설명합니다.",
        "highlights": [
            {
                "title": "은퇴 목적",
                "explanation": "연금계좌 중심의 실행 순서를 이해하기 쉽게 정리했습니다.",
                "evidence_codes": [evidence_code],
            },
            {
                "title": "장기 투자기간",
                "explanation": "장기 계획에 맞춘 점검 원칙을 설명합니다.",
                "evidence_codes": ["HORIZON_LONG"],
            },
        ],
        "caution": "시장 변동과 원금 손실 가능성을 함께 확인해야 합니다.",
    }
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(narrative)}],
            }
        ]
    }


@pytest.mark.asyncio
async def test_openai_explanation_uses_structured_grounded_request() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        assert request.headers["authorization"] == "Bearer test-openai-key"
        return httpx.Response(200, json=response_body())

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer test-openai-key"},
    ) as client:
        request = strategy_request()
        recommendation = strategy_service.recommend(request)
        result = await OpenAIStrategyExplanationService(
            openai_settings(), client
        ).explain(request, recommendation, "private-user-id")

    assert captured["store"] is False
    assert captured["model"] == "gpt-5.6"
    assert captured["safety_identifier"] == hashlib.sha256(
        b"private-user-id"
    ).hexdigest()
    assert "private-user-id" not in str(captured["input"])
    text_format = captured["text"]["format"]  # type: ignore[index]
    assert text_format["type"] == "json_schema"
    assert text_format["strict"] is True
    assert result.strategy_id == recommendation.strategy_id
    assert result.highlights[0].evidence_codes == ["GOAL_RETIREMENT"]


@pytest.mark.asyncio
async def test_openai_explanation_rejects_unknown_evidence_code() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body("MADE_UP_FACT"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        request = strategy_request()
        recommendation = strategy_service.recommend(request)
        service = OpenAIStrategyExplanationService(openai_settings(), client)
        with pytest.raises(StrategyExplanationFailed):
            await service.explain(request, recommendation, "user-id")


@pytest.mark.asyncio
async def test_openai_explanation_rejects_incomplete_response() -> None:
    body = response_body()
    body["status"] = "incomplete"

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        request = strategy_request()
        recommendation = strategy_service.recommend(request)
        service = OpenAIStrategyExplanationService(openai_settings(), client)
        with pytest.raises(StrategyExplanationFailed):
            await service.explain(request, recommendation, "user-id")
