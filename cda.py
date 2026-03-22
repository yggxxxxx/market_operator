from dataclasses import dataclass
from typing import Dict, List
from order_book import Order, OrderBook
from zip_strategy import ZIPStrategy, MarketSignal
from committed_trade import build_committed_trades, build_unmatched_orders


@dataclass
class MatchedRecord:
    match_id: str
    buyer_h_id: int
    seller_h_id: int
    buyer_order_id: str
    seller_order_id: str
    DateTime: str
    hour: int
    quantity_kwh: float
    matched_price_gbp_per_kwh: float
    trade_round: int


class CDA_mechanism:
    def __init__(
        self,
        order_book: OrderBook,
        zip_strategies: Dict[str, ZIPStrategy],
        max_trade_rounds: int = 150,
        max_no_trade_rounds: int = 50,
        verbose: bool = True,
    ):
        self.order_book = order_book
        self.zip_strategies = zip_strategies
        self.max_trade_rounds = max_trade_rounds
        self.max_no_trade_rounds = max_no_trade_rounds
        self.verbose = verbose

        self.matched_records: List[MatchedRecord] = []
        self.match_counter: int = 0

    def run_cda(self) -> dict:
        trade_round = 0
        no_trade_rounds = 0
        total_round = 0

        while True:
            total_round += 1

            best_bid = self.order_book.get_best_bid()
            best_ask = self.order_book.get_best_ask()

            if best_bid is None or best_ask is None:
                if self.verbose:
                    print("\n=== MARKET STOP ===")
                    print("No more orders on one side of the market.")
                break

            if self.verbose:
                self._print_iteration_header(total_round, no_trade_rounds)
                self._print_order_book_state("ORDER BOOK BEFORE MATCHING")

            if best_bid.submitted_price_gbp_per_kwh >= best_ask.submitted_price_gbp_per_kwh:
                if trade_round >= self.max_trade_rounds:
                    if self.verbose:
                        print("\n=== MARKET STOP ===")
                        print(f"Reached max_trade_rounds = {self.max_trade_rounds}")
                    break

                trade_round += 1
                no_trade_rounds = 0

                matched_price_gbp_per_kwh = self._determine_trade_price(best_bid, best_ask)
                matched_quantity_kwh = min(
                    best_bid.remaining_quantity_kwh,
                    best_ask.remaining_quantity_kwh
                )

                if self.verbose:
                    print("\nMATCH FOUND")
                    print(
                        f"buyer_order = {best_bid.order_id} (h_id={best_bid.h_id}, "
                        f"price={best_bid.submitted_price_gbp_per_kwh:.3f}, "
                        f"remaining_quantity_kwh={best_bid.remaining_quantity_kwh:.3f})"
                    )
                    print(
                        f"seller_order = {best_ask.order_id} (h_id={best_ask.h_id}, "
                        f"price={best_ask.submitted_price_gbp_per_kwh:.3f}, "
                        f"remaining_quantity_kwh={best_ask.remaining_quantity_kwh:.3f})"
                    )
                    print(f"matched_quantity_kwh = {matched_quantity_kwh:.3f}")
                    print(f"trade_price_gbp_per_kwh = {matched_price_gbp_per_kwh:.4f}")

                self._match_one_trade(
                    best_bid=best_bid,
                    best_ask=best_ask,
                    matched_price_gbp_per_kwh=matched_price_gbp_per_kwh,
                    trade_round=trade_round,
                )

                self.order_book.remove_filled_orders()

                if self.verbose:
                    print("\nUPDATING REMAINING ORDERS AFTER TRADE")
                self._update_orders_after_trade(
                    trade_price_gbp_per_kwh=matched_price_gbp_per_kwh
                )

                self.order_book.sort_book()

            else:
                no_trade_rounds += 1

                if self.verbose:
                    print("\nNO MATCH")
                    print(
                        f"best_bid_price = {best_bid.submitted_price_gbp_per_kwh:.4f}, "
                        f"best_ask_price = {best_ask.submitted_price_gbp_per_kwh:.4f}"
                    )
                    print("Update bids using best ask, and update asks using best bid.")

                if no_trade_rounds >= self.max_no_trade_rounds:
                    if self.verbose:
                        print("\n=== MARKET STOP ===")
                        print(f"Reached max_no_trade_rounds = {self.max_no_trade_rounds}")
                    break

                updated_any = self._update_orders_without_trade()

                self.order_book.remove_filled_orders()
                self.order_book.sort_book()

                if not updated_any:
                    if self.verbose:
                        print("\n=== MARKET STOP ===")
                        print("No order was updated in the no-trade round.")
                    break

        committed_trades = build_committed_trades(self.matched_records)

        unmatched_orders = self.order_book.get_all_bids() + self.order_book.get_all_asks()
        final_unmatched_orders = build_unmatched_orders(unmatched_orders)

        return {
            "matched_records": self.matched_records,
            "committed_trades": committed_trades,
            "unmatched_orders": final_unmatched_orders,
            "num_trades": len(committed_trades),
            "num_unmatched_orders": len(final_unmatched_orders),
        }

    def _match_one_trade(
        self,
        best_bid: Order,
        best_ask: Order,
        matched_price_gbp_per_kwh: float,
        trade_round: int,
    ) -> None:
        matched_quantity_kwh = min(
            best_bid.remaining_quantity_kwh,
            best_ask.remaining_quantity_kwh
        )

        self.match_counter += 1
        self.matched_records.append(
            MatchedRecord(
                match_id=f"M{self.match_counter}",
                buyer_h_id=best_bid.h_id,
                seller_h_id=best_ask.h_id,
                buyer_order_id=best_bid.order_id,
                seller_order_id=best_ask.order_id,
                DateTime=best_bid.DateTime,
                hour=best_bid.hour,
                quantity_kwh=matched_quantity_kwh,
                matched_price_gbp_per_kwh=matched_price_gbp_per_kwh,
                trade_round=trade_round,
            )
        )

        best_bid.remaining_quantity_kwh -= matched_quantity_kwh
        best_ask.remaining_quantity_kwh -= matched_quantity_kwh

    @staticmethod
    def _determine_trade_price(best_bid: Order, best_ask: Order) -> float:
        return (
            best_bid.submitted_price_gbp_per_kwh +
            best_ask.submitted_price_gbp_per_kwh
        ) / 2.0

    def _update_orders_after_trade(self, trade_price_gbp_per_kwh: float) -> None:
        all_orders = self.order_book.get_all_bids() + self.order_book.get_all_asks()

        for order in all_orders:
            if order.remaining_quantity_kwh <= 0:
                continue

            strategy = self.zip_strategies.get(order.order_id)
            if strategy is None:
                continue

            old_price = order.submitted_price_gbp_per_kwh

            strategy.update_from_market_signal(
                MarketSignal(
                    reference_price_gbp_per_kwh=trade_price_gbp_per_kwh,
                    accepted=True,
                    last_shout_type="bid"
                )
            )

            new_price = strategy.generate_shout(
                fit_price_gbp_per_kwh=strategy.fit_price_gbp_per_kwh,
                tou_price_gbp_per_kwh=strategy.tou_price_gbp_per_kwh
            )
            order.submitted_price_gbp_per_kwh = new_price

            if self.verbose:
                print(
                    f"h_id={order.h_id}, order_id={order.order_id}, side={order.side}, "
                    f"remaining_quantity_kwh={order.remaining_quantity_kwh:.3f}, "
                    f"price: {old_price:.3f} -> {new_price:.3f}"
                )

    def _update_orders_without_trade(self) -> bool:
        best_bid = self.order_book.get_best_bid()
        best_ask = self.order_book.get_best_ask()

        if best_bid is None or best_ask is None:
            return False

        updated_any = False
        reference_ask_price = best_ask.submitted_price_gbp_per_kwh
        reference_bid_price = best_bid.submitted_price_gbp_per_kwh

        for bid_order in self.order_book.get_all_bids():
            if bid_order.remaining_quantity_kwh <= 0:
                continue

            strategy = self.zip_strategies.get(bid_order.order_id)
            if strategy is None:
                continue

            old_price = bid_order.submitted_price_gbp_per_kwh

            strategy.update_from_market_signal(
                MarketSignal(
                    reference_price_gbp_per_kwh=reference_ask_price,
                    accepted=False,
                    last_shout_type="bid"
                )
            )

            new_price = strategy.generate_shout(
                fit_price_gbp_per_kwh=strategy.fit_price_gbp_per_kwh,
                tou_price_gbp_per_kwh=strategy.tou_price_gbp_per_kwh
            )
            bid_order.submitted_price_gbp_per_kwh = new_price
            updated_any = True

            if self.verbose:
                print(
                    f"h_id={bid_order.h_id}, order_id={bid_order.order_id}, side=buy, "
                    f"remaining_quantity_kwh={bid_order.remaining_quantity_kwh:.3f}, "
                    f"price: {old_price:.3f} -> {new_price:.3f}, "
                    f"reference_best_ask={reference_ask_price:.3f}"
                )

        for ask_order in self.order_book.get_all_asks():
            if ask_order.remaining_quantity_kwh <= 0:
                continue

            strategy = self.zip_strategies.get(ask_order.order_id)
            if strategy is None:
                continue

            old_price = ask_order.submitted_price_gbp_per_kwh

            strategy.update_from_market_signal(
                MarketSignal(
                    reference_price_gbp_per_kwh=reference_bid_price,
                    accepted=False,
                    last_shout_type="ask"
                )
            )

            new_price = strategy.generate_shout(
                fit_price_gbp_per_kwh=strategy.fit_price_gbp_per_kwh,
                tou_price_gbp_per_kwh=strategy.tou_price_gbp_per_kwh
            )
            ask_order.submitted_price_gbp_per_kwh = new_price
            updated_any = True

            if self.verbose:
                print(
                    f"h_id={ask_order.h_id}, order_id={ask_order.order_id}, side=sell, "
                    f"remaining_quantity_kwh={ask_order.remaining_quantity_kwh:.3f}, "
                    f"price: {old_price:.3f} -> {new_price:.3f}, "
                    f"reference_best_bid={reference_bid_price:.3f}"
                )

        return updated_any

    def _print_iteration_header(self, total_round: int, no_trade_rounds: int) -> None:
        print("\n" + "=" * 70)
        print(f"TOTAL ROUND {total_round}")
        print(f"no_trade_rounds = {no_trade_rounds}")
        print("=" * 70)

    def _print_order_book_state(self, title: str) -> None:
        print(f"\n=== {title} ===")

        print("BIDS")
        if not self.order_book.get_all_bids():
            print("[empty]")
        for order in self.order_book.get_all_bids():
            print(
                f"order_id={order.order_id}, h_id={order.h_id}, "
                f"price={order.submitted_price_gbp_per_kwh:.3f}, "
                f"remaining_quantity_kwh={order.remaining_quantity_kwh:.3f}"
            )

        print("\nASKS")
        if not self.order_book.get_all_asks():
            print("[empty]")
        for order in self.order_book.get_all_asks():
            print(
                f"order_id={order.order_id}, h_id={order.h_id}, "
                f"price={order.submitted_price_gbp_per_kwh:.3f}, "
                f"remaining_quantity_kwh={order.remaining_quantity_kwh:.3f}"
            )