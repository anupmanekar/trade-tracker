from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"

class Force(str, Enum):
    GTC = "gtc"  # Good till cancelled
    POST_ONLY = "post_only"  # Post only
    FOK = "fok"  # Fill or kill
    IOC = "ioc"  # Immediate or cancel

class TpslType(str, Enum):
    NORMAL = "normal"  # SPOT order (default)
    TPSL = "tpsl"  # SPOT TP/SL order

class StpMode(str, Enum):
    NONE = "none"  # Not setting STP (default)
    CANCEL_TAKER = "cancel_taker"  # Cancel taker order
    CANCEL_MAKER = "cancel_maker"  # Cancel maker order
    CANCEL_BOTH = "cancel_both"  # Cancel both taker and maker orders

class PlaceOrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair name, e.g. BTCUSDT")
    side: OrderSide = Field(..., description="Order Direction: buy or sell")
    order_type: OrderType = Field(..., alias="orderType", description="Order type: limit or market")
    force: Force = Field(..., description="Execution strategy (invalid when orderType is market)")
    size: str = Field(..., description="Amount - for Limit/Market-Sell: base coins, for Market-Buy: quote coins")
    price: Optional[str] = Field(None, description="Limit price (decimal places per Get Symbol Info interface)")
    client_oid: Optional[str] = Field(None, alias="clientOid", description="Custom order ID (invalid when tpslType is tpsl)")
    trigger_price: Optional[str] = Field(None, alias="triggerPrice", description="SPOT TP/SL trigger price, only required in SPOT TP/SL order")
    tpsl_type: Optional[TpslType] = Field(TpslType.NORMAL, alias="tpslType", description="Order type: normal (SPOT order) or tpsl (SPOT TP/SL order)")
    request_time: Optional[str] = Field(None, alias="requestTime", description="Request Time, Unix millisecond timestamp")
    receive_window: Optional[str] = Field(None, alias="receiveWindow", description="Valid time window, Unix millisecond timestamp")
    stp_mode: Optional[StpMode] = Field(StpMode.NONE, alias="stpMode", description="STP Mode (Self Trade Prevention)")
    preset_take_profit_price: Optional[str] = Field(None, alias="presetTakeProfitPrice", description="Take profit price (invalid when tpslType is tpsl)")
    execute_take_profit_price: Optional[str] = Field(None, alias="executeTakeProfitPrice", description="Take profit execute price (invalid when tpslType is tpsl)")
    preset_stop_loss_price: Optional[str] = Field(None, alias="presetStopLossPrice", description="Stop loss price (invalid when tpslType is tpsl)")
    execute_stop_loss_price: Optional[str] = Field(None, alias="executeStopLossPrice", description="Stop loss execute price (invalid when tpslType is tpsl)")