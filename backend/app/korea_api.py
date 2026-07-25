
import os
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import redis.asyncio as redis

# Configuration from environment variables
APP_KEY = os.environ.get("KOREA_INVEST_APP_KEY")
APP_SECRET = os.environ.get("KOREA_INVEST_APP_SECRET")
API_BASE_URL = (
    "https://openapivts.koreainvestment.com:29443"
    if os.environ.get("KIS_ENVIRONMENT", "virtual") == "virtual"
    else "https://openapi.koreainvestment.com:9443"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

class KoreaInvestAPI:
    _instance = None
    _redis_client: Optional[redis.Redis] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KoreaInvestAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 
"_initialized"): # Ensure initialization only once
            self.access_token = None
            self.token_expired_at = None
            self.last_auth_attempt = None
            self._initialized = True
            self.lock = asyncio.Lock()

    async def _get_redis_client(self) -> redis.Redis:
        if self._redis_client is None:
            self._redis_client = redis.from_url(REDIS_URL)
        return self._redis_client

    async def _call_api(self, method: str, path: str, headers: Dict = None, json_data: Dict = None, params: Dict = None) -> Dict:
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/{path}"
            async with session.request(method, url, headers=headers, json=json_data, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def _get_access_token(self) -> str:
        headers = {
            "content-type": "application/json"
        }
        json_data = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }
        response = await self._call_api("POST", "oauth2/tokenP", headers=headers, json_data=json_data)
        self.access_token = response["access_token"]
        expires_in = response["expires_in"]
        self.token_expired_at = datetime.now() + timedelta(seconds=expires_in - 60) # 1분 여유있게 만료
        return self.access_token

    async def get_bearer_token(self) -> str:
        async with self.lock:
            if not self.access_token or (self.token_expired_at and datetime.now() >= self.token_expired_at):
                print("[*] Issuing a new access token...")
                await self._get_access_token()
            return self.access_token

    async def get_ws_token(self) -> str:
        # 웹소켓 토큰은 별도로 발급받아야 함. 여기서는 예시로 access_token 재활용 또는 별도 발급 로직 추가 필요
        # 실제로는 웹소켓용 토큰 발급 API를 호출해야 합니다.
        # 예를 들어, '/oauth2/Approval' 같은 API를 통해 웹소켓 키를 발급받을 수 있습니다.
        print("[*] Issuing a new websocket token...")
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {await self.get_bearer_token()}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": "UAPAT00001000" # WebSocket Approval Key
        }
        json_data = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }
        # This is a placeholder. Actual WS token might require different endpoint/payload.
        response = await self._call_api("POST", "oauth2/Approval", headers=headers, json_data=json_data) # This endpoint might be different for actual WS token
        return response["approval_key"]

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        token = await self.get_bearer_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": "FHKST01010100" # 주식 현재가 일별
        }
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol
        }
        response = await self._call_api("GET", "uapi/domestic-stock/v1/quotations/inquire-price", headers=headers, params=params)
        return response

    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        token = await self.get_bearer_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": "FHKST01010200" # 주식 현재가 호가
        }
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol
        }
        response = await self._call_api("GET", "uapi/domestic-stock/v1/quotations/inquire-asking-price", headers=headers, params=params)
        return response

class PriceDistributor:
    _instance = None
    _redis_client: Optional[redis.Redis] = None
    _api_client: Optional[KoreaInvestAPI] = None
    _update_task: Optional[asyncio.Task] = None
    _symbols_to_track: set = set()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PriceDistributor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"): # Ensure initialization only once
            self._initialized = True

    async def _get_redis_client(self) -> redis.Redis:
        if self._redis_client is None:
            self._redis_client = redis.from_url(REDIS_URL)
        return self._redis_client

    async def _get_api_client(self) -> KoreaInvestAPI:
        if self._api_client is None:
            self._api_client = KoreaInvestAPI()
        return self._api_client

    def add_symbol(self, symbol: str):
        self._symbols_to_track.add(symbol)

    def remove_symbol(self, symbol: str):
        self._symbols_to_track.discard(symbol)

    async def _update_prices_task(self):
        api_client = await self._get_api_client()
        redis_client = await self._get_redis_client()
        while True:
            for symbol in list(self._symbols_to_track):
                try:
                    current_price = await api_client.get_current_price(symbol)
                    order_book = await api_client.get_order_book(symbol)
                    await redis_client.set(f"price:{symbol}", json.dumps(current_price)) 
                    await redis_client.set(f"orderbook:{symbol}", json.dumps(order_book))
                    print(f"[*] Cached data for {symbol}")
                except Exception as e:
                    print(f"[!] Error fetching data for {symbol}: {e}")
            await asyncio.sleep(1) # Update every 1 second

    async def start_update_scheduler(self):
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.create_task(self._update_prices_task())
            print("[!] PriceDistributor scheduler started.")

    async def stop_update_scheduler(self):
        if self._update_task:
            self._update_task.cancel()
            await self._update_task
            self._update_task = None
            print("[!] PriceDistributor scheduler stopped.")

    async def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        redis_client = await self._get_redis_client()
        price_data = await redis_client.get(f"price:{symbol}")
        if price_data:
            return json.loads(price_data.decode("utf-8"))
        return None

    async def get_cached_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        redis_client = await self._get_redis_client()
        order_book_data = await redis_client.get(f"orderbook:{symbol}")
        if order_book_data:
            return json.loads(order_book_data.decode("utf-8"))
        return None

# Example usage in FastAPI (assuming main.py imports this)
# from korea_api import KoreaInvestAPI, PriceDistributor
#
# @app.on_event("startup")
# async def startup_event():
#     price_distributor = PriceDistributor()
#     price_distributor.add_symbol("005930") # Samsung Electronics
#     await price_distributor.start_업데이트_스케줄러()
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     price_distributor = PriceDistributor()
#     await price_distributor.stop_업데이트_스케줄러()
#
# @app.get("/stock/{symbol}/price")
# async def get_stock_price(symbol: str):
#     distributor = PriceDistributor()
#     cached_price = await distributor.get_cached_price(symbol)
#     if cached_price:
#         return {"symbol": symbol, "price": cached_price, "source": "cache"}
#     return {"symbol": symbol, "message": "Price not yet cached"}
