from decimal import Decimal

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import MarketDataError
from app.integrations.kis.client import KisClient
from app.services.market import KisMarketDataProvider


def kis_settings() -> Settings:
    return Settings(
        market_data_provider="kis",
        kis_environment="paper",
        kis_app_key="test-key",
        kis_app_secret="test-secret",
        _env_file=None,
    )


@pytest.mark.asyncio
async def test_kis_provider_maps_domestic_overseas_and_exchange_rate() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth2/tokenP":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path.endswith("/domestic-stock/v1/quotations/inquire-price"):
            assert request.headers["tr_id"] == "FHKST01010100"
            assert request.url.params["FID_INPUT_ISCD"] == "005930"
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output": {
                        "stck_prpr": "82400",
                        "prdy_vrss": "500",
                        "prdy_vrss_sign": "2",
                        "prdy_ctrt": "0.61",
                    },
                },
            )
        if request.url.path.endswith("/overseas-price/v1/quotations/price"):
            assert request.headers["tr_id"] == "HHDFS00000300"
            assert request.url.params["EXCD"] == "NAS"
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output": {
                        "last": "219.31",
                        "diff": "2.00",
                        "sign": "5",
                        "rate": "0.92",
                    },
                },
            )
        if request.url.path.endswith("/overseas-price/v1/quotations/price-detail"):
            assert request.headers["tr_id"] == "HHDFS76200200"
            return httpx.Response(200, json={"rt_cd": "0", "output": {"t_rate": "1385.20"}})
        raise AssertionError(f"Unexpected request: {request.url}")

    client = KisClient(kis_settings(), transport=httpx.MockTransport(handler))
    provider = KisMarketDataProvider(kis_settings(), client)

    domestic = await provider.get_quote("005930")
    overseas = await provider.get_quote("AAPL")
    exchange_rate = await provider.get_exchange_rate("USD", "KRW")

    assert domestic is not None
    assert domestic.price == Decimal("82400")
    assert domestic.change == Decimal("500")
    assert domestic.currency == "KRW"
    assert overseas is not None
    assert overseas.price == Decimal("219.31")
    assert overseas.change == Decimal("-2.00")
    assert overseas.change_rate == Decimal("-0.92")
    assert exchange_rate is not None
    assert exchange_rate.rate == Decimal("1385.20")
    assert exchange_rate.source == "kis"
    assert sum(request.url.path == "/oauth2/tokenP" for request in requests) == 1
    assert all(
        request.headers.get("authorization") == "Bearer token-1"
        for request in requests
        if request.url.path != "/oauth2/tokenP"
    )


@pytest.mark.asyncio
async def test_kis_client_surfaces_api_error_message() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        return httpx.Response(200, json={"rt_cd": "1", "msg_cd": "EGW00123", "msg1": "조회 실패"})

    client = KisClient(kis_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(MarketDataError, match="조회 실패"):
        await client.get_domestic_quote("005930")


@pytest.mark.asyncio
async def test_kis_provider_maps_daily_candles() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path.endswith("/domestic-stock/v1/quotations/inquire-daily-itemchartprice"):
            assert request.headers["tr_id"] == "FHKST03010100"
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output2": [
                        {
                            "stck_bsop_date": "20260725",
                            "stck_oprc": "82000",
                            "stck_hgpr": "83000",
                            "stck_lwpr": "81000",
                            "stck_clpr": "82400",
                            "acml_vol": "1000000",
                        },
                        {
                            "stck_bsop_date": "20260724",
                            "stck_oprc": "81000",
                            "stck_hgpr": "82500",
                            "stck_lwpr": "80500",
                            "stck_clpr": "82000",
                            "acml_vol": "900000",
                        },
                    ],
                },
            )
        if request.url.path.endswith("/overseas-price/v1/quotations/dailyprice"):
            assert request.headers["tr_id"] == "HHDFS76240000"
            assert request.url.params["EXCD"] == "NAS"
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output2": [
                        {
                            "xymd": "20260725",
                            "open": "220.00",
                            "high": "223.00",
                            "low": "219.50",
                            "clos": "222.00",
                            "tvol": "123456",
                        }
                    ],
                },
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = KisClient(kis_settings(), transport=httpx.MockTransport(handler))
    provider = KisMarketDataProvider(kis_settings(), client)

    domestic = await provider.get_candles("005930", 10)
    overseas = await provider.get_candles("AAPL", 10)

    assert domestic is not None
    assert [candle.date.isoformat() for candle in domestic.candles] == ["2026-07-24", "2026-07-25"]
    assert domestic.candles[-1].close == Decimal("82400")
    assert overseas is not None
    assert overseas.candles[0].close == Decimal("222.00")


@pytest.mark.asyncio
async def test_kis_provider_maps_domestic_and_overseas_orderbooks() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path.endswith("/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"):
            assert request.headers["tr_id"] == "FHKST01010200"
            assert request.url.params["FID_INPUT_ISCD"] == "005930"
            output = {
                "total_askp_rsqn": "5500",
                "total_bidp_rsqn": "6500",
            }
            for level in range(1, 11):
                output[f"askp{level}"] = str(82400 + level * 100)
                output[f"askp_rsqn{level}"] = str(level * 100)
                output[f"bidp{level}"] = str(82400 - level * 100)
                output[f"bidp_rsqn{level}"] = str(level * 120)
            return httpx.Response(200, json={"rt_cd": "0", "output1": output})
        if request.url.path.endswith("/overseas-price/v1/quotations/inquire-asking-price"):
            assert request.headers["tr_id"] == "HHDFS76200100"
            assert request.url.params["EXCD"] == "NAS"
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output1": {
                        "pask": "219.32",
                        "pbid": "219.30",
                        "vask": "120",
                        "vbid": "95",
                    },
                },
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = KisClient(kis_settings(), transport=httpx.MockTransport(handler))
    provider = KisMarketDataProvider(kis_settings(), client)

    domestic = await provider.get_orderbook("005930")
    overseas = await provider.get_orderbook("AAPL")

    assert domestic is not None
    assert len(domestic.asks) == len(domestic.bids) == 10
    assert domestic.asks[0].price == Decimal("82500")
    assert domestic.bids[0].price == Decimal("82300")
    assert domestic.total_ask_quantity == Decimal("5500")
    assert overseas is not None
    assert overseas.asks[0].price == Decimal("219.32")
    assert overseas.bids[0].quantity == Decimal("95")


@pytest.mark.asyncio
async def test_kis_provider_maps_security_overview_metrics() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        if request.url.path.endswith("/domestic-stock/v1/quotations/inquire-price"):
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output": {
                        "stck_oprc": "82000",
                        "stck_hgpr": "83000",
                        "stck_lwpr": "81000",
                        "acml_vol": "1234567",
                        "w52_hgpr": "90000",
                        "w52_lwpr": "60000",
                        "per": "18.5",
                        "pbr": "1.7",
                        "eps": "4454.05",
                        "bps": "48470.59",
                    },
                },
            )
        if request.url.path.endswith("/overseas-price/v1/quotations/price"):
            return httpx.Response(
                200,
                json={
                    "rt_cd": "0",
                    "output": {
                        "open": "218.00",
                        "high": "221.50",
                        "low": "217.20",
                        "tvol": "987654",
                        "h52p": "260.10",
                        "l52p": "169.21",
                        "perx": "31.4",
                        "pbrx": "45.2",
                        "epsx": "6.98",
                        "bpsx": "4.85",
                    },
                },
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    client = KisClient(kis_settings(), transport=httpx.MockTransport(handler))
    provider = KisMarketDataProvider(kis_settings(), client)

    domestic = await provider.get_overview("005930")
    overseas = await provider.get_overview("AAPL")

    assert domestic is not None
    assert domestic.volume == Decimal("1234567")
    assert domestic.per == Decimal("18.5")
    assert domestic.week_52_high == Decimal("90000")
    assert overseas is not None
    assert overseas.pbr == Decimal("45.2")
    assert overseas.week_52_low == Decimal("169.21")
