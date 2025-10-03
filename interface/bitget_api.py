import time
import requests
import json
import os
from dotenv import load_dotenv
from domain.models import PlaceOrderRequest
from utils.bitget_signature_utils import generate_signature, get_timestamp
import logging

load_dotenv()
# Configure logger
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BITGET_COIN_API = "https://api.bitget.com/api/v2/spot/public/coins?coin={coin}"
BITGET_SYMBOL_API = "https://api.bitget.com/api/v2/spot/public/symbols?symbol={symbol}"
BITGET_TICKER_API = "https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}"
BITGET_PLACE_ORDER_API = "https://api.bitget.com/api/v2/spot/trade/place-order"
BITGET_ORDER_INFO_API = "https://api.bitget.com/api/v2/spot/trade/orderInfo?orderId={order_id}"
BITGET_GET_ACCOUNT_ASSETS_API = "https://api.bitget.com/api/v2/spot/account/assets"

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

def get_headers(timestamp, signature):
    return {
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": str(timestamp),
        "ACCESS-PASSPHRASE": API_PASSPHRASE
    }

def get_coin_info(coin):
    url = BITGET_COIN_API.format(coin=coin)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        logger.info(json.dumps(data, indent=4))
    else:
        logger.error("Error fetching data from Bitget API")

def get_symbol_info(symbol):
    url = BITGET_SYMBOL_API.format(symbol=symbol)
    response = requests.get(url)
    if response.status_code == 200:         
        data = response.json()
        logger.info(json.dumps(data))
        return data
    else:
        logger.error("Error fetching data from Bitget API")

def get_ticker_info(symbol):
    url = BITGET_TICKER_API.format(symbol=symbol)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        #print("Hello from trade-tracker!")
        #print(json.dumps(data, indent=4))
        return data
    else:
        logger.error("Error fetching data from Bitget API")
        return None

def get_current_price_for_ticker(symbol) -> float:
    ticker_info = get_ticker_info(symbol)
    if ticker_info and 'data' in ticker_info:
        for item in ticker_info['data']:
            if item['symbol'] == symbol:
                return float(item['lastPr'])
    return None

def get_history_candlestick_data(symbol, granularity, endtime, size=100):
    print(f"Fetching historical candlestick data for {symbol}, granularity: {granularity}, endtime: {endtime}, size: {size}")
    url = f"https://api.bitget.com/api/v2/spot/market/history-candles?symbol={symbol}&granularity={granularity}&limit={size}&endTime={endtime}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logger.error("Error fetching data from Bitget API with error: %s", response.text)
        return None

def place_order(order_request: PlaceOrderRequest) -> dict:
    logger.info("Placing order with the following details: %s", order_request.model_dump_json())
    url = BITGET_PLACE_ORDER_API
    timestamp = get_timestamp()
    relativeUrl = "/api/v2/spot/trade/place-order"
    signature = generate_signature(API_SECRET, timestamp, "POST", relativeUrl, body=order_request.model_dump_json(exclude_none=True))
    headers = get_headers(timestamp, signature)
    response = requests.post(url, headers=headers, data=order_request.model_dump_json(exclude_none=True))
    if response.status_code == 200:
        data = response.json()
        logger.info("Order placed successfully: %s", json.dumps(data))
        return data
    else:
        logger.error("Error placing order: %s", response.text)
        return {"status": "error", "message": response.text}

def get_order_info(order_id: str) -> dict:
    logger.info("Getting Order Info for order ID: %s", order_id)
    url = BITGET_ORDER_INFO_API.format(order_id=order_id)
    timestamp = get_timestamp()
    relativeUrl = f"/api/v2/spot/trade/orderInfo"
    signature = generate_signature(API_SECRET, timestamp, "GET", relativeUrl, params={"orderId": order_id})
    headers = get_headers(timestamp, signature)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # logger.info("Order Information fetched successfully: %s", json.dumps(data))
        return data
    else:
        logger.error("Error fetching order information: %s", response.text)
        return {"status": "error", "message": response.text}

def get_account_assets(coin: str = None) -> dict:
    logger.info("Fetching account assets...")
    url = BITGET_GET_ACCOUNT_ASSETS_API
    if coin:
        url += f"?coin={coin}"
    timestamp = get_timestamp()
    relativeUrl = "/api/v2/spot/account/assets"
    signature = generate_signature(API_SECRET, timestamp, "GET", relativeUrl, params={"coin": coin} if coin else None)
    headers = get_headers(timestamp, signature)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        #logger.info("Account assets fetched successfully: %s", json.dumps(data))
        assets_dict = {}
        for asset in data.get('data', []):
            coin = asset.get('coin')
            if coin:
                assets_dict[coin] = {
                    'available': float(asset['available']),
                    'frozen': float(asset['frozen']),
                    'locked': float(asset['locked']),
                    'limitAvailable': float(asset['limitAvailable']),
                    'uTime': asset['uTime']
                }
        #logger.info("Parsed account assets: %s", json.dumps(assets_dict))
        return assets_dict
    else:
        logger.error("Error fetching account assets: %s", response.text)
        return {"status": "error", "message": response.text}
    
def cancel_order_by_symbol(symbol: str) -> dict:
    logger.info("Cancelling all open orders for symbol: %s", symbol)
    url = "https://api.bitget.com/api/v2/spot/trade/cancel-symbol-order"
    timestamp = get_timestamp()
    relativeUrl = "/api/v2/spot/trade/cancel-symbol-order"
    body = {"symbol": symbol}
    signature = generate_signature(API_SECRET, timestamp, "POST", relativeUrl, body=json.dumps(body))
    headers = get_headers(timestamp, signature)
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        data = response.json()
        logger.info("All open orders cancelled successfully: %s", json.dumps(data))
        return data
    else:
        logger.error("Error cancelling orders: %s", response.text)
        return {"status": "error", "message": response.text}

def get_current_plan_orders() -> dict:
    logger.info("Fetching current plan orders...")
    url = "https://api.bitget.com/api/v2/spot/trade/history-orders?symbol=JUPUSDT"
    timestamp = get_timestamp()
    relativeUrl = "/api/v2/spot/trade/history-orders"
    signature = generate_signature(API_SECRET, timestamp, "GET", relativeUrl, params={"symbol": "JUPUSDT"})
    headers = get_headers(timestamp, signature)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        logger.info("Current plan orders fetched successfully: %s", json.dumps(data))
        return data
    else:
        logger.error("Error fetching current plan orders: %s", response.text)
        return {"status": "error", "message": response.text}