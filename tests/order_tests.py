import pprint
from interface.bitget_api import cancel_order_by_symbol, get_current_plan_orders, place_order, get_account_assets
from domain.models import PlaceOrderRequest
from order_message_processor import scalping_strategy

if __name__ == "__main__":
    symbol = "XCXUSDT"
    price = 0.05652
    side = "sell"
    order_type = "limit"
    order_quantity = 35.3
    #get_account_assets()
    #scalping_strategy(symbol, price, side, order_type)
    #get_current_plan_orders()
    # sell_order_request = PlaceOrderRequest(
    #     symbol=symbol,
    #     size=str(order_quantity),
    #     side="sell",
    #     orderType="limit",
    #     price=str(round((price * 1.01), 5)),  # Target 1% profit
    #     force="gtc",
    # )
    # response = place_order(sell_order_request)
    def truncate_float(value, decimals):
        factor = 10 ** decimals
        return int(value * factor) / factor

    print(truncate_float(35.3646, 2))
