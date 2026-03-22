from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Order:
    order_id: str
    h_id: int
    DateTime: str
    hour: int
    side: str
    quantity_kwh: float
    remaining_quantity_kwh: float
    limit_price_gbp_per_kwh: float
    submitted_price_gbp_per_kwh: float

    def __post_init__(self):
        if self.side not in {"buy", "sell"}:
            raise ValueError(f"side must be 'buy' or 'sell', got {self.side}")

        if self.quantity_kwh < 0:
            raise ValueError("quantity_kwh must be >= 0")

        if self.remaining_quantity_kwh < 0:
            raise ValueError("remaining_quantity_kwh must be >= 0")

        if self.limit_price_gbp_per_kwh < 0:
            raise ValueError("limit_price_gbp_per_kwh must be >= 0")

        if self.submitted_price_gbp_per_kwh < 0:
            raise ValueError("submitted_price_gbp_per_kwh must be >= 0")


class OrderBook:

    def __init__(self):
        self.bids: List[Order] = []
        self.asks: List[Order] = []

    def add_order(self, order: Order) -> None:
        if order.side == "buy":
            self.bids.append(order)
            self.sort_bids()
        else:
            self.asks.append(order)
            self.sort_asks()

    def sort_bids(self) -> None:
        self.bids.sort(
            key=lambda o: (-o.submitted_price_gbp_per_kwh, -o.remaining_quantity_kwh)
        )

    def sort_asks(self) -> None:
        self.asks.sort(
            key=lambda o: (o.submitted_price_gbp_per_kwh, -o.remaining_quantity_kwh)
        )

    def sort_book(self) -> None:
        self.sort_bids()
        self.sort_asks()

    def get_best_bid(self) -> Optional[Order]:
        return self.bids[0] if self.bids else None

    def get_best_ask(self) -> Optional[Order]:
        return self.asks[0] if self.asks else None

    def has_match(self) -> bool:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid is None or best_ask is None:
            return False

        return best_bid.submitted_price_gbp_per_kwh >= best_ask.submitted_price_gbp_per_kwh

    def remove_filled_orders(self) -> None:
        self.bids = [o for o in self.bids if o.remaining_quantity_kwh > 0]
        self.asks = [o for o in self.asks if o.remaining_quantity_kwh > 0]

    def get_all_bids(self) -> List[Order]:
        return list(self.bids)

    def get_all_asks(self) -> List[Order]:
        return list(self.asks)

    def summary(self) -> dict:
        return {
            "num_bids": len(self.bids),
            "num_asks": len(self.asks),
            "best_bid": (self.bids[0].submitted_price_gbp_per_kwh if self.bids else None),
            "best_ask": (self.asks[0].submitted_price_gbp_per_kwh if self.asks else None),
        }

    def print_book(self) -> None:
        print("=== BIDS ===")
        for order in self.bids:
            print(f"order_id={order.order_id}, h_id={order.h_id}, price={order.submitted_price_gbp_per_kwh:.4f},remaining_quantity_kwh={order.remaining_quantity_kwh:.4f}")

        print("\n=== ASKS ===")
        for order in self.asks:
            print(f"order_id={order.order_id}, h_id={order.h_id}, price={order.submitted_price_gbp_per_kwh:.4f}, remaining_quantity_kwh={order.remaining_quantity_kwh:.4f}")