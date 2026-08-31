import hashlib
import json

import httpx

from app.core.config import Settings, get_settings
from app.schemas.strategy import (
    StrategyExplanationNarrative,
    StrategyExplanationResponse,
    StrategyRequest,
    StrategyResponse,
)

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
EXPLANATION_DISCLAIMER = (
    "AI는 규칙 엔진이 계산한 결과를 설명할 뿐 비중·금액·세율을 계산하거나 "
    "투자 결정을 대신하지 않습니다."
)


class StrategyExplanationUnavailable(RuntimeError):
    pass


class StrategyExplanationFailed(RuntimeError):
    pass


class OpenAIStrategyExplanationService:
    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client

    async def explain(
        self,
        request: StrategyRequest,
        recommendation: StrategyResponse,
        user_id: str,
    ) -> StrategyExplanationResponse:
        if self.settings.ai_provider != "openai" or not self.settings.openai_api_key:
            raise StrategyExplanationUnavailable("AI 전략 설명이 설정되지 않았습니다.")

        payload = self._request_payload(request, recommendation, user_id)
        headers = {
            "Authorization": (
                f"Bearer {self.settings.openai_api_key.get_secret_value()}"
            )
        }
        try:
            if self.client is not None:
                response = await self.client.post(
                    OPENAI_RESPONSES_URL,
                    json=payload,
                    headers=headers,
                )
            else:
                async with httpx.AsyncClient(
                    timeout=self.settings.ai_request_timeout_seconds,
                ) as client:
                    response = await client.post(
                        OPENAI_RESPONSES_URL,
                        json=payload,
                        headers=headers,
                    )
            response.raise_for_status()
            narrative = StrategyExplanationNarrative.model_validate_json(
                self._output_text(response.json())
            )
            self._validate_evidence_codes(narrative, recommendation)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise StrategyExplanationFailed("AI 전략 설명을 생성하지 못했습니다.") from exc

        return StrategyExplanationResponse(
            **narrative.model_dump(),
            engine_version=recommendation.engine_version,
            strategy_id=recommendation.strategy_id,
            provider="openai",
            model=self.settings.openai_model,
            disclaimer=EXPLANATION_DISCLAIMER,
        )

    def _request_payload(
        self,
        request: StrategyRequest,
        recommendation: StrategyResponse,
        user_id: str,
    ) -> dict[str, object]:
        return {
            "model": self.settings.openai_model,
            "instructions": (
                "당신은 한국어 금융 교육 설명자입니다. 제공된 규칙 엔진 결과만 "
                "쉽게 풀어 설명하세요. 새로운 비중, 금액, 수익률, 세율, 상품이나 "
                "사실을 만들지 마세요. 각 핵심 설명은 반드시 제공된 reason code를 "
                "evidence_codes에 인용하세요. 투자 권유나 수익 보장을 하지 마세요."
            ),
            "input": json.dumps(
                {
                    "request": request.model_dump(mode="json"),
                    "recommendation": recommendation.model_dump(mode="json"),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "strategy_explanation",
                    "strict": True,
                    "schema": StrategyExplanationNarrative.model_json_schema(),
                }
            },
            "max_output_tokens": 900,
            "store": False,
            "safety_identifier": hashlib.sha256(user_id.encode("utf-8")).hexdigest(),
        }

    @staticmethod
    def _output_text(body: dict[str, object]) -> str:
        if body.get("status") != "completed":
            raise ValueError("OpenAI response did not complete.")
        for item in body.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    text = content.get("text")
                    if isinstance(text, str):
                        return text
        raise ValueError("OpenAI response did not contain output text.")

    @staticmethod
    def _validate_evidence_codes(
        narrative: StrategyExplanationNarrative,
        recommendation: StrategyResponse,
    ) -> None:
        allowed = set(recommendation.reason_codes)
        cited = {
            code
            for highlight in narrative.highlights
            for code in highlight.evidence_codes
        }
        if not cited.issubset(allowed):
            raise ValueError("AI explanation cited an unknown reason code.")


strategy_explanation_service = OpenAIStrategyExplanationService()
