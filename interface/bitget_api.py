import requests
import json
import os
from domain.models import PlaceOrderRequest
from utils.bitget_signature_utils import generate_signature, get_timestamp


BITGET_COIN_API = "https://api.bitget.com/api/v2/spot/public/coins?coin={coin}"
BITGET_SYMBOL_API = "https://api.bitget.com/api/v2/spot/public/symbols?symbol={symbol}"
BITGET_TICKER_API = "https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}"
BITGET_PLACE_ORDER_API = "https://api.bitget.com/api/v2/spot/trade/place-order"
BITGET_ORDER_INFO_API = "https://api.bitget.com/api/v2/spot/trade/orderInfo?orderId={order_id}"

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

def get_coin_info(coin):
    url = BITGET_COIN_API.format(coin=coin)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Hello from trade-tracker!")
        print(json.dumps(data, indent=4))
    else:
        print("Error fetching data from Bitget API")

def get_symbol_info(symbol):
    url = BITGET_SYMBOL_API.format(symbol=symbol)
    response = requests.get(url)
    if response.status_code == 200:         
        data = response.json()
        print("Hello from trade-tracker!")
        print(json.dumps(data, indent=4))
        return data
    else:
        print("Error fetching data from Bitget API")

def get_ticker_info(symbol):
    url = BITGET_TICKER_API.format(symbol=symbol)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        #print("Hello from trade-tracker!")
        #print(json.dumps(data, indent=4))
        return data
    else:
        print("Error fetching data from Bitget API")
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
        #print(json.dumps(data, indent=4))
        return data
    else:
        print("Error fetching data from Bitget API with error:", response.text)
        return None

def place_order(order_request: PlaceOrderRequest) -> dict:
    print("Placing order with the following details:", order_request.model_dump_json())
    url = BITGET_PLACE_ORDER_API
    timestamp = get_timestamp()
    signature = generate_signature(API_SECRET, timestamp, "POST", url, body=order_request.model_dump_json())
    headers = {
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE
    }
    response = requests.post(url, headers=headers, data=order_request.model_dump_json())
    if response.status_code == 200:
        data = response.json()
        print("Order placed successfully:")
        print(json.dumps(data, indent=4))
        return data
    else:
        print("Error placing order:", response.text)
        return {"status": "error", "message": response.text}

def get_order_info(order_id: str) -> dict:
    print(f"Checking status for order ID: {order_id}")
    url = BITGET_ORDER_INFO_API.format(order_id=order_id)
    timestamp = get_timestamp()
    signature = generate_signature(API_SECRET, timestamp, "GET", url, params={"orderId": order_id})
    headers = {
        "Content-Type": "application/json",
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("Order status fetched successfully:")
        print(json.dumps(data, indent=4))
        return data
    else:
        print("Error fetching order status:", response.text)
        return {"status": "error", "message": response.text}