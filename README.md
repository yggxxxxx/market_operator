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
