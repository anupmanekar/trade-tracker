import requests
import json
import time

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

if __name__ == "__main__":
    # Program will accept ticker symbol as input
    ticker_symbol = input("Enter the ticker symbol (e.g., SUIUSDT): ")
    # Get price info at interval of 1 minute for SUIUSDT ticker and print it. Do this for 10 times.
    # if price has increased between two intervals is more than 1% and this happens for 3 consecutive intervals, print a buy alert message.

    previous_price = 0
    consecutive_increases = 0
    for i in range(60):
        price = get_current_price_for_ticker(ticker_symbol)
        print(f"Time {i} : Current price for {ticker_symbol}: {price}")
        if previous_price is not None and price is not None:
            price_change = price - previous_price
            if price_change >= previous_price * 0.01:  # Check for 1% increase
                consecutive_increases += 1
                if consecutive_increases >= 3:
                    print(f"Buy alert: Price increased more than 1% for {ticker_symbol} for 3 consecutive intervals.")
            else:
                consecutive_increases = 0
        previous_price = price
        time.sleep(60)  # wait for 1 minute before next check

