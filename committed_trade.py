from dataclasses import dataclass
from typing import List


@dataclass
class CommittedTrade:
    trade_id: str
    buyer_h_id: int
    seller_h_id: int
    buyer_order_id: str
    seller_order_id: str
    DateTime: str
    hour: int
    quantity_kwh: float
    trade_price_gbp_per_kwh: float
    trade_value_gbp: float
    trade_round: int


@dataclass
class UnmatchedOrder:
    unmatched_order_id: str
    order_id: str
    h_id: int
    DateTime: str
    hour: int
    side: str
    original_quantity_kwh: float
    remaining_quantity_kwh: float
    limit_price_gbp_per_kwh: float
    submitted_price_gbp_per_kwh: float


def build_committed_trades(matched_records: List) -> List[CommittedTrade]:
    committed_trades: List[CommittedTrade] = []

    for i, matched in enumerate(matched_records, start=1):
        committed_trades.append(
            CommittedTrade(
                trade_id=f"T{i}",
                buyer_h_id=matched.buyer_h_id,
                seller_h_id=matched.seller_h_id,
                buyer_order_id=matched.buyer_order_id,
                seller_order_id=matched.seller_order_id,
                DateTime=matched.DateTime,
                hour=matched.hour,
                quantity_kwh=matched.quantity_kwh,
                trade_price_gbp_per_kwh=matched.matched_price_gbp_per_kwh,
                trade_value_gbp=matched.quantity_kwh * matched.matched_price_gbp_per_kwh,
                trade_round=matched.trade_round,
            )
        )

    return committed_trades


def build_unmatched_orders(unmatched_orders: List) -> List[UnmatchedOrder]:
    final_unmatched_orders: List[UnmatchedOrder] = []

    for i, order in enumerate(unmatched_orders, start=1):
        final_unmatched_orders.append(
            UnmatchedOrder(
                unmatched_order_id=f"U{i}",
                order_id=order.order_id,
                h_id=order.h_id,
                DateTime=order.DateTime,
                hour=order.hour,
                side=order.side,
                original_quantity_kwh=order.quantity_kwh,
                remaining_quantity_kwh=order.remaining_quantity_kwh,
                limit_price_gbp_per_kwh=order.limit_price_gbp_per_kwh,
                submitted_price_gbp_per_kwh=order.submitted_price_gbp_per_kwh,
            )
        )

    return final_unmatched_orders


def committed_trades_to_dicts(committed_trades: List[CommittedTrade]) -> List[dict]:
    return [
        {
            "trade_id": trade.trade_id,
            "buyer_h_id": trade.buyer_h_id,
            "seller_h_id": trade.seller_h_id,
            "buyer_order_id": trade.buyer_order_id,
            "seller_order_id": trade.seller_order_id,
            "DateTime": trade.DateTime,
            "hour": trade.hour,
            "quantity_kwh": trade.quantity_kwh,
            "trade_price_gbp_per_kwh": trade.trade_price_gbp_per_kwh,
            "trade_value_gbp": trade.trade_value_gbp,
            "trade_round": trade.trade_round,
        }
        for trade in committed_trades
    ]


def unmatched_orders_to_dicts(unmatched_orders: List[UnmatchedOrder]) -> List[dict]:
    return [
        {
            "unmatched_order_id": order.unmatched_order_id,
            "order_id": order.order_id,
            "h_id": order.h_id,
            "DateTime": order.DateTime,
            "hour": order.hour,
            "side": order.side,
            "original_quantity_kwh": order.original_quantity_kwh,
            "remaining_quantity_kwh": order.remaining_quantity_kwh,
            "limit_price_gbp_per_kwh": order.limit_price_gbp_per_kwh,
            "submitted_price_gbp_per_kwh": order.submitted_price_gbp_per_kwh,
        }
        for order in unmatched_orders
    ]