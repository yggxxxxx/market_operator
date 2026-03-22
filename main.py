import pandas as pd

from tariff import load_tou_profile, load_fit_profile
from zip_strategy import ZIPStrategy
from order_book import Order, OrderBook
from cda import CDA_mechanism


def generate_orders_and_zip_strategies(test_df: pd.DataFrame, tou_profile, fit_profile):
    order_book = OrderBook()
    zip_strategies = {}

    order_counter = 0

    for _, row in test_df.iterrows():
        h_id = int(row["h_id"])
        DateTime = row["DateTime"]
        hour = pd.to_datetime(DateTime).hour

        import_energy = float(row["import_energy"])
        export_energy = float(row["export_energy"])

        fit_price_gbp_per_kwh = fit_profile.get_price(hour)
        tou_price_gbp_per_kwh = tou_profile.get_price(hour)

        if import_energy > 0:
            side = "buy"
            quantity_kwh = import_energy
            limit_price_gbp_per_kwh = tou_price_gbp_per_kwh

            order_counter += 1
            order_id = f"O{order_counter}"

            zip_strategies[order_id] = ZIPStrategy(h_id=h_id, side=side)

            submitted_price_gbp_per_kwh = zip_strategies[order_id].generate_shout(
                fit_price_gbp_per_kwh=fit_price_gbp_per_kwh,
                tou_price_gbp_per_kwh=tou_price_gbp_per_kwh
            )

            order = Order(
                order_id=order_id,
                h_id=h_id,
                DateTime=DateTime,
                hour=hour,
                side=side,
                quantity_kwh=quantity_kwh,
                remaining_quantity_kwh=quantity_kwh,
                limit_price_gbp_per_kwh=limit_price_gbp_per_kwh,
                submitted_price_gbp_per_kwh=submitted_price_gbp_per_kwh,
            )
            order_book.add_order(order)

        elif export_energy > 0:
            side = "sell"
            quantity_kwh = export_energy
            limit_price_gbp_per_kwh = fit_price_gbp_per_kwh

            order_counter += 1
            order_id = f"O{order_counter}"

            zip_strategies[order_id] = ZIPStrategy(h_id=h_id, side=side)

            submitted_price_gbp_per_kwh = zip_strategies[order_id].generate_shout(
                fit_price_gbp_per_kwh=fit_price_gbp_per_kwh,
                tou_price_gbp_per_kwh=tou_price_gbp_per_kwh
            )

            order = Order(
                order_id=order_id,
                h_id=h_id,
                DateTime=DateTime,
                hour=hour,
                side=side,
                quantity_kwh=quantity_kwh,
                remaining_quantity_kwh=quantity_kwh,
                limit_price_gbp_per_kwh=limit_price_gbp_per_kwh,
                submitted_price_gbp_per_kwh=submitted_price_gbp_per_kwh,
            )
            order_book.add_order(order)

    return order_book, zip_strategies


def print_test_households(test_df: pd.DataFrame) -> None:
    print("=== TEST HOUSEHOLDS ===")
    print(test_df[[
        "DateTime",
        "h_id",
        "demand",
        "pv",
        "battery_charged",
        "battery_discharged",
        "energy_before",
        "energy_after",
        "import_energy",
        "export_energy",
        "soc"
    ]])


def print_initial_order_book(order_book: OrderBook) -> None:
    print("\n=== INITIAL ORDER BOOK ===")
    order_book.print_book()


def print_results(result: dict) -> None:
    print("\n=== COMMITTED TRADES ===")
    if not result["committed_trades"]:
        print("[empty]")
    for trade in result["committed_trades"]:
        print(
            f"trade_id={trade.trade_id}, "
            f"buyer_h_id={trade.buyer_h_id}, seller_h_id={trade.seller_h_id}, "
            f"buyer_order_id={trade.buyer_order_id}, seller_order_id={trade.seller_order_id}, "
            f"DateTime={trade.DateTime}, hour={trade.hour}, "
            f"quantity_kwh={trade.quantity_kwh:.3f}, "
            f"trade_price_gbp_per_kwh={trade.trade_price_gbp_per_kwh:.4f}, "
            f"trade_value_gbp={trade.trade_value_gbp:.4f}, "
            f"trade_round={trade.trade_round}"
        )

    print("\n=== UNMATCHED ORDERS ===")
    if not result["unmatched_orders"]:
        print("[empty]")
    for order in result["unmatched_orders"]:
        print(
            f"unmatched_order_id={order.unmatched_order_id}, "
            f"order_id={order.order_id}, h_id={order.h_id}, "
            f"DateTime={order.DateTime}, hour={order.hour}, side={order.side}, "
            f"original_quantity_kwh={order.original_quantity_kwh:.3f}, "
            f"remaining_quantity_kwh={order.remaining_quantity_kwh:.3f}, "
            f"limit_price_gbp_per_kwh={order.limit_price_gbp_per_kwh:.4f}, "
            f"submitted_price_gbp_per_kwh={order.submitted_price_gbp_per_kwh:.4f}"
        )

    print("\n=== SUMMARY ===")
    print(f"num_trades = {result['num_trades']}")
    print(f"num_unmatched_orders = {result['num_unmatched_orders']}")


def main(test_df: pd.DataFrame):
    if test_df is None or test_df.empty:
        raise ValueError("test_df is empty")

    print_test_households(test_df)

    tou_profile = load_tou_profile()
    fit_profile = load_fit_profile()

    order_book, zip_strategies = generate_orders_and_zip_strategies(
        test_df=test_df,
        tou_profile=tou_profile,
        fit_profile=fit_profile
    )

    print_initial_order_book(order_book)

    mechanism = CDA_mechanism(
        order_book=order_book,
        zip_strategies=zip_strategies,
        max_trade_rounds=150,
        max_no_trade_rounds=30,
        verbose=True,
    )

    result = mechanism.run_cda()
    print_results(result)
    return result


if __name__ == "__main__":
    from test_household import generate_test_households

    test_df = generate_test_households(
        num_households=20,
        DateTime="2026-01-01 18:00:00"
    )

    main(test_df)