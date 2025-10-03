# Read the message from Redis queue and track the buy order and poll the symbol until the price increases by 5% or decreases by 2%
import logging
from math import floor
import redis
import json
import time
from interface.bitget_api import cancel_order_by_symbol, get_ticker_info, place_order, get_order_info, get_account_assets, get_symbol_info
from domain.models import PlaceOrderRequest
import pprint
import threading

# Configure logger
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

MAX_TRADING_AMOUNT = 2  # Maximum USDT to use for trading
polling_symbols = []  # List to keep track of symbols being polled

def truncate_float(value, decimals):
        factor = 10 ** decimals
        return int(value * factor) / factor

# def poll_price(symbol, order_price):
#     polling_interval = 60  # 1 minute
#     max_attempts = 15
#     attempts = 0
#     while attempts < max_attempts:
#         attempts += 1
#         time.sleep(polling_interval)
#         ticker_info = get_ticker_info(symbol)
#         if ticker_info and 'data' in ticker_info and len(ticker_info['data']) > 0:
#             last_price = float(ticker_info['data'][0]['lastPr'])
#             print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Current price for {symbol}: {last_price}")
#             if last_price >= order_price * 1.02:
#                 print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 2% Target Reached {symbol}.")
#                 break
#             elif last_price <= order_price * 0.98:
#                 print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 2% Stop Loss Reached {symbol}.")
#                 break
#             else:
#                 print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Price change for {symbol} is within range.")
#         else:
#             print(f"Could not fetch ticker info for {symbol}.")
#     if (attempts == max_attempts):
#         profit_loss = ((last_price - order_price) / order_price) * 100 if last_price else 0
#         print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Max attempts reached for {symbol}. Selling at market price. P/L: {profit_loss:.2f}%")

#     polling_symbols.remove(symbol)

def scalping_strategy(symbol, price, side="buy", order_type="limit"):
    symbol_info = get_symbol_info(symbol)
    quantity_precision = int(symbol_info['data'][0]['quantityPrecision']) if symbol_info and 'data' in symbol_info and 'quantityPrecision' in symbol_info['data'][0] else 2  # Default precision
    price_precision = int(symbol_info['data'][0]['pricePrecision']) if symbol_info and 'data' in symbol_info and 'pricePrecision' in symbol_info['data'][0] else 2  # Default precision
    latest_price_for_symbol = get_ticker_info(symbol=symbol)
    order_price = float(latest_price_for_symbol['data'][0]['lastPr']) if latest_price_for_symbol and 'data' in latest_price_for_symbol and len(latest_price_for_symbol['data']) > 0 else price
    logger.info(f"Placing order for {symbol} at latest price {order_price}")
    order_quantity = round(MAX_TRADING_AMOUNT/order_price, quantity_precision)
    sell_order_id = None
    order_request = PlaceOrderRequest(
        symbol=symbol,
        price=str(order_price),
        size=str(order_quantity),
        side=side,
        orderType=order_type,
        force="gtc",
        tpslType="normal",
        #presetTakeProfitPrice=str(round(order_price * 1.02, 5)),
        #presetStopLossPrice=str(round(order_price * 0.98, 5)),
    )
    sell_order_request = PlaceOrderRequest(
        symbol=symbol,
        size=str(order_quantity),
        side="sell",
        orderType="limit",
        price=str(round(order_price * 1.01, price_precision)),  # Target 2% profit
        force="gtc",
        tpslType="normal",
    )
    response = place_order(order_request)
    order_info = None
    if response and response.get('code') == '00000':
        logger.info(f"Order placed successfully for {symbol}.")
        start_time = time.time()
        while True:
            time.sleep(30)  # Poll every 30 seconds
            order_info = get_order_info(response['data']['orderId'])
            if order_info and order_info['data'][0]['status'] in ['filled']:
                logger.info(f"Order status for {symbol} is filled.")
                logger.info(f"Placing sell order for {symbol} at price {sell_order_request.price}")
                coin_assets = get_account_assets(symbol[:-4])
                sell_order_request.size = str(truncate_float(float(coin_assets[symbol[:-4]]['available']), quantity_precision))  # Update sell size to available balance
                sell_response = place_order(sell_order_request)
                if sell_response and sell_response.get('code') == '00000':
                    sell_order_id = sell_response['data']['orderId']
                    logger.info(f"Sell order placed successfully for {symbol}. Sell Order ID: {sell_order_id}")
                else:
                    logger.error(f"Failed to place sell order for {symbol}: {sell_response}")
                break
            if time.time() - start_time > 300:  # 5 minutes
                logger.warning(f"Order for {symbol} not filled in 5 minutes. Cancelling order.")
                cancel_order_by_symbol(symbol)
                break
    else:
        logger.error(f"Failed to place order for {symbol}: {response}")
    if order_info is not None and order_info['data'][0]['status'] in ['filled'] and sell_order_id is not None:
        get_order_info(response['data']['orderId'])
        #sell_the_placed_order(order_price, symbol)
        wait_for_sell_and_place_market_order(sell_order_id, order_price, symbol)
    polling_symbols.remove(symbol)

# def sell_the_placed_order(order_price, symbol):
#     # Sell the asset when it crosses 2% profit or 1% loss
#     account_assets = get_account_assets()
#     coin = symbol[:-4]
#     if (account_assets[coin]['frozen'] is None) or (float(account_assets[coin]['frozen']) < 0.01) and (float(account_assets[coin]['available']) < 0.01):
#         logger.warning(f"No {coin} balance available to sell.")
#         return
#     available_balance = f"{account_assets[coin]['available']}"
#     logger.info(f"Available balance for {coin}: {available_balance}")
#     # Loop for max 15 minutes and check the price every 1 minute
#     polling_interval = 60  # 1 minute
#     max_attempts = 15
#     attempts = 0
#     sell_at_market = False
#     limit_sell_price = 0
#     while attempts < max_attempts:
#         attempts += 1
#         ticker_info = get_ticker_info(symbol)
#         if ticker_info and 'data' in ticker_info and len(ticker_info['data']) > 0:
#             last_price = float(ticker_info['data'][0]['lastPr'])
#             logger.info(f"Current price for {symbol}: {last_price}")
#             if last_price >= order_price * 1.02:
#                 logger.info(f"2% Target Reached {symbol}. Selling at market price.")
#                 sell_at_market = True
#                 break
#             elif last_price <= order_price * 0.99:
#                 logger.info(f"1% Stop Loss Reached {symbol}. Selling at market price.")
#                 sell_at_market = True
#                 break
#             else:
#                 logger.info(f"Price change for {symbol} is within range.")
#         else:
#             logger.error(f"Could not fetch ticker info for {symbol}.")
#         time.sleep(polling_interval)

#     if (attempts == max_attempts):
#         sell_at_market = True
#         logger.warning(f"Max attempts reached for {symbol}. Selling at market price.")

#     if sell_at_market:
#         sell_order_request = PlaceOrderRequest(
#             symbol=symbol,
#             size=str(float(available_balance)),  # Sell all available
#             side="sell",
#             orderType="market",
#             force="gtc",
#             tpslType="normal",
#         )
#         sell_response = place_order(sell_order_request)
#         logger.info(f"Sell order response: {sell_response}")

def wait_for_sell_and_place_market_order(sell_order_id, buy_price, symbol):
    polling_interval = 60  # 60 seconds
    max_attempts = 20  # Poll for max 20 minutes
    attempts = 0
    coin = symbol[:-4]
    sell_at_market = False
    order_info = None
    while not sell_at_market and attempts < max_attempts:
        attempts += 1
        # Check if the sell order is filled
        if sell_order_id is None:
            logger.error(f"No sell order ID provided for {symbol}. Exiting.")
            return
        order_info = get_order_info(sell_order_id)
        if order_info and 'data' in order_info and len(order_info['data']) > 0:
            if order_info['data'][0]['status'] in ['filled']:
                logger.info(f"Sell order for {symbol} is filled.")
                return
            else:
                logger.info(f"Sell order status for {symbol}: {order_info['data'][0]['status']}")
        else:
            logger.error(f"Could not fetch order info for sell order ID {sell_order_id}.")
        ticker_info = get_ticker_info(symbol)
        # if latest price drops below 1% of buy price, cancel the sell order and place market sell order
        if ticker_info and 'data' in ticker_info and len(ticker_info['data']) > 0:
            last_price = float(ticker_info['data'][0]['lastPr'])
            logger.info(f"Current price for {symbol}: {last_price}")
            if last_price <= buy_price * 0.99:
                logger.info(f"Price dropped below 1% of buy price for {symbol}. Cancelling sell order and placing market sell order.")
                sell_at_market = True
                break
        time.sleep(polling_interval)
    if (attempts == max_attempts or sell_at_market):
        logger.warning(f"Max attempts reached for {symbol} or sell at market triggered. Cancelling any open orders.")
        cancel_order_by_symbol(symbol)
        logger.info(f"Selling at market price.")
        #time.sleep(50)  # Wait for 5 seconds before placing sell order
        #account_assets = get_account_assets(coin)
        available_balance = order_info['data'][0]['size'] if order_info and 'data' in order_info and len(order_info['data']) > 0 else 0
        logger.info(f"Available balance for {coin}: {available_balance}")
        if available_balance is None or float(available_balance) < 0.01:
            logger.warning(f"No {coin} balance available to sell.")
            return
        sell_order_request = PlaceOrderRequest(
            symbol=symbol,
            size=str(available_balance),  # Sell all available
            side="sell",
            orderType="market",
            force="gtc",
            tpslType="normal",
        )
        sell_response = place_order(sell_order_request)
        pprint.pprint(sell_response)


def main():
    # Connect to Redis (default localhost:6379)
    r = redis.Redis(host='localhost', port=6379, db=0)
    place_order_queue = 'place_order_requests'  # Queue to place order requests
    logger.info("Listening for messages... (Ctrl+C to stop)")
    try:
        while True:
            # BLPOP blocks until a message is available
            message = r.blpop(place_order_queue)
            if message:
                logger.info(f"Received message at {time.strftime('%Y-%m-%d %H:%M:%S')}: {message[1].decode('utf-8')}")
                # Process the message (for example, fetch historical candlestick data)
                msg_data = json.loads(message[1].decode('utf-8'))
                symbol = msg_data.get('symbol')
                order_price = msg_data.get('price', 0)
                account_assets = get_account_assets()
                # for testing add USDT balance. Comment this in production
                #account_assets['usdt']['available'] = 5
                if not symbol:
                    logger.warning("No symbol found in message.")
                    continue
                if (symbol not in polling_symbols) and (account_assets['USDT']['available'] >= MAX_TRADING_AMOUNT):
                #if (symbol not in polling_symbols):
                    logger.info(f"Order price for {symbol}: {order_price}")
                    polling_symbols.append(symbol)
                    polling_thread = threading.Thread(target=scalping_strategy, args=(symbol, order_price))
                    polling_thread.start()
                else:
                    logger.warning(f"Already polling {symbol} or insufficient USDT balance.")
    except KeyboardInterrupt:
        logger.info("Stopping message processor.")

if __name__ == "__main__":
    main()