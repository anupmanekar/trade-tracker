# Read the message from Redis queue and track the buy order and poll the symbol until the price increases by 5% or decreases by 2%
import redis
import json
import time
from interface.bitget_api import get_ticker_info
import pprint
import threading

polling_symbols = []  # List to keep track of symbols being polled

def poll_price(symbol, order_price):
    polling_interval = 60  # 1 minute
    max_attempts = 15
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        time.sleep(polling_interval)
        ticker_info = get_ticker_info(symbol)
        if ticker_info and 'data' in ticker_info and len(ticker_info['data']) > 0:
            last_price = float(ticker_info['data'][0]['lastPr'])
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Current price for {symbol}: {last_price}")
            if last_price >= order_price * 1.02:
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 2% Target Reached {symbol}.")
                break
            elif last_price <= order_price * 0.98:
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 2% Stop Loss Reached {symbol}.")
                break
            else:
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Price change for {symbol} is within range.")
        else:
            print(f"Could not fetch ticker info for {symbol}.")
    if (attempts == max_attempts):
        profit_loss = ((last_price - order_price) / order_price) * 100 if last_price else 0
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Max attempts reached for {symbol}. Selling at market price. P/L: {profit_loss:.2f}%")

    polling_symbols.remove(symbol)

def main():
    # Connect to Redis (default localhost:6379)
    r = redis.Redis(host='localhost', port=6379, db=0)
    place_order_queue = 'place_order_requests'  # Queue to place order requests
    print("Listening for messages... (Ctrl+C to stop)")
    try:
        while True:
            # BLPOP blocks until a message is available
            message = r.blpop(place_order_queue)
            if message:
                print(f"Received message at {time.strftime('%Y-%m-%d %H:%M:%S')}: {message[1].decode('utf-8')}")
                # Process the message (for example, fetch historical candlestick data)
                msg_data = json.loads(message[1].decode('utf-8'))
                symbol = msg_data.get('symbol')
                order_price = msg_data.get('price', 0)
                if not symbol:
                    print("No symbol found in message.")
                    continue
                if symbol not in polling_symbols:
                    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Order price for {symbol}: {order_price}")
                    polling_symbols.append(symbol)
                    polling_thread = threading.Thread(target=poll_price, args=(symbol, order_price))
                    polling_thread.start()
    except KeyboardInterrupt:
        print("Stopping message processor.")

if __name__ == "__main__":
    main()