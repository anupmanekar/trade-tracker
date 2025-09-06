import requests
import json
import time
import threading

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
    all_ticker_data = get_ticker_info("")  # Test call to ensure function works
    # create a multithreaded logic where price of each symbol from all_ticker_data is fetched on a separate thread every 5 seconds
    # and the price is printed to the console
    # Make this round-robin so that each symbol is fetched in a separate thread on separate intervals
    # Improve the logic to fetch the price for each symbol at 1 min interval and print buy alert for each symbol when the price is changing more than 1% for 3 consecutive intervals.
    # Send the buy alert to redis queue
    # Use redis queue to store the buy alerts and process them in a separate thread
    # Use redis pubsub to send the buy alerts to a websocket server
    # Use a websocket client to connect to the websocket server and print the buy alerts to the console

    symbols = [item['symbol'] for item in all_ticker_data['data'] if 'USDT' in item['symbol']] if all_ticker_data and 'data' in all_ticker_data else []
    #symbols = symbols[:10]

    interval = 0.5  # seconds

    def fetch_price_with_delay(symbol, delay):
        time.sleep(delay)
        price_history = []
        counter = 0
        while True:
            counter += 1
            price = get_current_price_for_ticker(symbol)
            if price is None or price == 0.0:
                print(f"Error fetching price for {symbol}")
                time.sleep(interval * len(symbols))
                continue
            print(f"{counter} Current price for {symbol}: {price}")
            price_history.append(price)
            if len(price_history) > 4:
                price_history.pop(0)
            if len(price_history) == 4:
                # Check if price changed more than 1% for last 3 consecutive intervals
                alerts = [
                    abs(price_history[i+1] - price_history[i]) / price_history[i] > 0.01
                    for i in range(3)
                ]
                if all(alerts):
                    print(f"Buy alert for {symbol}: Price changed more than 1% for 3 consecutive intervals:", price_history)
            time.sleep(interval * len(symbols))

    for idx, symbol in enumerate(symbols):
        thread = threading.Thread(target=fetch_price_with_delay, args=(symbol, idx * interval))
        thread.start()
