import time
from interface.bitget_api import get_ticker_info, get_current_price_for_ticker
import redis
import json
import pprint

import logging

# Configure logger
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":

    # Call get_ticker_info to fetch all ticker data at interval of 1 minute and filter symbols with USDT and volume > 1,000,000 and extract symbol, price, volume
    # Store the latest 4 prices for each symbol and if the price changes more than 1% for 3 consecutive intervals, print a buy alert message
    # Do not call get_ticker_info for each symbol, call it once and create object arrays with symbol, price, volume

    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_queue = "buy_alerts"  # Redis list name for buy alerts

    symbol_price_history = {}
    interval_count = 0
    interval = 20  # seconds, 20 second interval
    while True:
        interval_count += 1
        all_ticker_data = get_ticker_info("")  # Test call to ensure function works
        # Create dictonary with symbol as key and price history as value
        for item in all_ticker_data.get('data', []):
            if item['symbol'][-4:] == 'USDT' and float(item.get('usdtVolume', 0)) > 200_000:
                if item['symbol'] not in symbol_price_history:
                    symbol_price_history[item['symbol']] = []
                symbol_price_history[item['symbol']].append(float(item['lastPr']))
        if interval_count == 1:
            logger.info(f"Fetched {len(symbol_price_history)} symbols with USDT volume > 200,000")
        logger.info(f"Interval {interval_count}: Current symbol price history:")
        #pprint.pprint(symbol_price_history, sort_dicts=False, indent=2)

        # Generate buy alerts and send it to redis for symbols with price change > 1% for 3 consecutive intervals
        for symbol, prices in symbol_price_history.items():
            #print(f"Latest price {symbol}: {symbol_price_history[symbol][-1]}")
            if len(prices) > 4:
                symbol_price_history[symbol].pop(0)
                alerts = [
                    (symbol_price_history[symbol][i+1] - symbol_price_history[symbol][i]) / symbol_price_history[symbol][i] > 0.003
                    for i in range(3)
                ]
                if all(alerts):
                    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    alert = {
                        "symbol": symbol,
                        "prices": symbol_price_history[symbol].copy(),
                        "message": f"Buy alert for {symbol}: Price changed >1% for 3 consecutive intervals",
                        "timestamp": current_time
                    }
                    logger.info(f"Generated alert: {alert}")
                    redis_client.rpush(redis_queue, json.dumps(alert))
        time.sleep(interval)  # Wait for 60 seconds

    

    