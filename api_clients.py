import requests
import json


BITGET_COIN_API = "https://api.bitget.com/api/v2/spot/public/coins?coin={coin}"
BITGET_SYMBOL_API = "https://api.bitget.com/api/v2/spot/public/symbols?symbol={symbol}"
BITGET_TICKER_API = "https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}"

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