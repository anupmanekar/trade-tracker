import redis
import time
from interface.bitget_api import get_history_candlestick_data
import json

def main():
    # Connect to Redis (default localhost:6379)
    r = redis.Redis(host='localhost', port=6379, db=0)
    queue_name = 'buy_alerts'  # Change this to your queue name
    place_order_queue = 'place_order_requests'  # Queue to place order requests

    print("Listening for messages... (Ctrl+C to stop)")
    try:
        while True:
            # BLPOP blocks until a message is available
            message = r.blpop(queue_name)
            if message:
                # log current time and message
                # message is a tuple: (queue_name, message_data)
                print(f"Received message at {time.strftime('%Y-%m-%d %H:%M:%S')}: {message[1].decode('utf-8')}")
                # Process the message (for example, fetch historical candlestick data)
                msg_data = json.loads(message[1].decode('utf-8'))
                symbol = msg_data.get('symbol')
                if not symbol:
                    print("No symbol found in message.")
                    continue
                # Fetch historical candlestick data for the symbol
                endtime = int(time.time() * 1000)  # current time in milliseconds
                granularity = "1min"  # 1 minute candles
                size = 10  # last 10 candles
                candles = get_history_candlestick_data(symbol, granularity, endtime, size)
                # Based on the candles data for last 3 closing prices of array, determine if the price is in uptrend or downtrend

                if candles and 'data' in candles:
                    closing_prices = [float(candle[4]) for candle in candles['data']]
                    open_prices = [float(candle[1]) for candle in candles['data']]
                    high_prices = [float(candle[2]) for candle in candles['data']]
                    low_prices = [float(candle[3]) for candle in candles['data']]
                    trading_vol_usdt = [float(candle[6]) for candle in candles['data']]
                    if len(closing_prices) >= 3:
                        # Calculate trend based on multiple factors: open, close, high, low, volume
                        recent_opens = open_prices[-3:]
                        recent_closes = closing_prices[-3:]
                        #recent_highs = high_prices[-3:]
                        #recent_lows = low_prices[-3:]
                        recent_volumes = trading_vol_usdt[-3:]

                        uptrend = (
                            all(recent_closes[i] > recent_opens[i] for i in range(3)) and
                            recent_closes[-1] > recent_closes[-2] > recent_closes[-3] and
                            #recent_highs[-1] > recent_highs[-2] > recent_highs[-3] and
                            #recent_lows[-1] > recent_lows[-2] > recent_lows[-3] and
                            recent_volumes[-1] >= recent_volumes[-2] >= recent_volumes[-3]
                        )
                        downtrend = (
                            all(recent_closes[i] < recent_opens[i] for i in range(3)) and
                            recent_closes[-1] < recent_closes[-2] < recent_closes[-3] and
                            #recent_highs[-1] < recent_highs[-2] < recent_highs[-3] and
                            #recent_lows[-1] < recent_lows[-2] < recent_lows[-3] and
                            recent_volumes[-1] <= recent_volumes[-2] <= recent_volumes[-3]
                        )

                        trend = None
                        order = None

                        if uptrend:
                            trend = "uptrend"
                            order = {
                                "symbol": symbol,
                                "side": "buy",
                                "type": "limit",
                                "quantity": 1,  # Placeholder quantity
                                "price": recent_closes[-1]  # Placeholder price
                            }
                        elif downtrend:
                            trend = "downtrend"
                        else:
                            trend = "sideways"
                            order = {
                                "symbol": symbol,
                                "side": "buy",
                                "type": "limit",
                                "quantity": 1,  # Placeholder quantity
                                "price": recent_closes[-1]  # Placeholder price
                            }

                        print(f"Trend: {trend}")
                        print(f"Last 3 opens: {recent_opens}")
                        print(f"Last 3 closes: {recent_closes}")
                        print(f"Last 3 USDT volumes: {recent_volumes}")

                        # Only place order for uptrend or sideways
                        if order:
                            r.rpush(place_order_queue, json.dumps(order))
                            print(f"Order placed: {order}")
                    else:
                        print("Not enough data to determine trend.")
                else:
                    print("No candlestick data received.")
    except KeyboardInterrupt:
        print("\nStopped listening.")

if __name__ == "__main__":
    main()