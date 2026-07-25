from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import MarketDataError


class KisClient:
    """Thin async client for KIS REST endpoints.

    Token persistence, throttling and websocket distribution are intentionally
    left for the dedicated market-data phase.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.kis_app_key or not settings.kis_app_secret:
            raise ValueError("KIS_APP_KEY와 KIS_APP_SECRET이 필요합니다.")
        self._settings = settings
        self._base_url = (
            "https://openapivts.koreainvestment.com:29443"
            if settings.kis_environment == "paper"
            else "https://openapi.koreainvestment.com:9443"
        )
        self._access_token: str | None = None
        self._expires_at: datetime | None = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        tr_id: str | None = None,
        params: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        headers = {
            "content-type": "application/json",
            "appkey": self._settings.kis_app_key or "",
            "appsecret": self._settings.kis_app_secret or "",
        }
        if authenticated:
            headers["authorization"] = f"Bearer {await self.get_access_token()}"
        if tr_id:
            headers["tr_id"] = tr_id

        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
                response = await client.request(method, path, headers=headers, params=params, json=json)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MarketDataError(f"KIS 요청 실패: {path}") from exc

    async def get_access_token(self) -> str:
        now = datetime.now(UTC)
        if self._access_token and self._expires_at and now < self._expires_at:
            return self._access_token
        response = await self._request(
            "POST",
            "/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self._settings.kis_app_key or "",
                "appsecret": self._settings.kis_app_secret or "",
            },
            authenticated=False,
        )
        self._access_token = str(response["access_token"])
        expires_in = int(response.get("expires_in", 86_400))
        self._expires_at = now + timedelta(seconds=max(60, expires_in - 60))
        return self._access_token

    async def get_domestic_quote(self, symbol: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol,
            },
        )

    async def get_domestic_orderbook(self, symbol: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol,
            },
        )
