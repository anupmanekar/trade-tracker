import time
import threading
from api_clients import get_ticker_info, get_current_price_for_ticker
import redis
import json

if __name__ == "__main__":
    all_ticker_data = get_ticker_info("")  # Test call to ensure function works

    symbols = [item['symbol'] for item in all_ticker_data['data'] if 'USDT' in item['symbol']] if all_ticker_data and 'data' in all_ticker_data else []
    interval = 60  # seconds, 1 minute interval

    # Initialize Redis connection
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_queue = "buy_alerts"

    def fetch_price_with_delay(symbol, delay):
        time.sleep(delay)
        price_history = []
        while True:
            price = get_current_price_for_ticker(symbol)
            if price is None or price == 0.0:
                print(f"Error fetching price for {symbol}")
                time.sleep(interval)
                continue
            print(f"Current price for {symbol}: {price}")
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
                    alert = {
                        "symbol": symbol,
                        "prices": price_history.copy(),
                        "message": f"Buy alert for {symbol}: Price changed >1% for 3 consecutive intervals"
                    }
                    redis_client.rpush(redis_queue, json.dumps(alert))
                    print(f"Buy alert sent to Redis for {symbol}: {alert}")
            time.sleep(interval)

    for idx, symbol in enumerate(symbols):
        thread = threading.Thread(target=fetch_price_with_delay, args=(symbol, idx * 2))
        thread.daemon = True
        thread.start()
