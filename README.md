The Market Operator is responsible for the P2P market-clearing process in the local energy trading system.

It takes the net electricity position of each household in each timeslot (`import_energy` / `export_energy`), generates bid and ask orders, applies the ZIP pricing strategy within the tariff bounds, and clears the market through a Continuous Double Auction (CDA), and outputs the transaction results and unmatched orders.

Files
- main.py — main entry point for running market sessions
- cda.py — Continuous Double Auction (CDA) clearing mechanism
- zip_strategy.py — ZIP-based pricing strategy for bid/ask generation
- order_book.py — order book data structure and sorting logic
- tariff.py — ToU / FiT tariff loading
- committed_trade.py — formatting of matched trades and unmatched orders
- test_household.py — test household data generation for standalone debugging
 
Expected input
- `DateTime`
- `h_id`
- `import_energy`
- `export_energy`

Expected output
- `matched_records` — raw matching records produced during the CDA process
- `committed_trades` — finalized trade records, including buyer ID, seller ID, quantity, trade price, and trade value
- `unmatched_orders` — remaining unmatched orders after market clearing, including fully unmatched orders and partially filled residual orders
- `num_trades` — total number of committed trades
- `num_unmatched_orders` — total number of unmatched orders

When integrated into the full system, the market module will keep only the core order generation and market-clearing functionality, while pricing logic, tariff data, and household test generation will be provided by other modules.
- zip_strategy.py will be moved to the Household Agent module
- tariff.py will be moved to the Main Grid module
- test_household.py will be removed


Update

zip_strategy.py
- bidirectional conversion between margin and price, `price_from_margin()` and `margin_from_price()`
- added a target-price generation function `target_price()`
- update mechanism `update_from_market_signal()`
- new parameter ranges, the `c` parameter, `last_delta`
These modifications have made the pricing logic more modular and closer to a structured ZIP learning process

cda.py
- the old version linked ZIP strategies through `order_id`, while the new version uses `trader_registry` and `trader_key` to manage trader state
- separates buyer-side and seller-side update logic, making post-trade and no-trade order updates more explicit

order_book.py
- add `trader_key`, `submission_seq`, and `submission_counter` to track trader identity and order submission order
- in the old version, orders with the same price were prioritised by remaining quantity, the new version changes this to submission order, making the book to the price-time priority, follow FIFO

main.py
- the old version supported a single market-clearing run for one timeslot, while the new version adds `gen_orders_and_slot()`, `run_one_slot()`, and `run_market_sessions()` to support multi-timeslot market sessions
- add `trader_registry` and `trader_key`, so ZIP trader state is no longer managed only at the individual-order level and can be reused more naturally across timeslots

test_household.py
- changed from random test data generation to fixed test data

update
zip_strategy.py
- line 8 c range changes from 0-0.05 to 0-0.03
- line 41 change bid to ask
- line 52 change ask to bid
- line 112 target price

cda.py
- line 26/27 change the number of round
- line 195 change ask to bid
- line 227 change bid to ask
- line 270 change ask to bid
- line 305 change bid to ask

main.py
- line 170/171 change the number of round

ToU/FiT data source: change to the London data
