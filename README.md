Market Operator

This code is the "market" part of the P2P power trading system. It generates buy and sell orders based on the "import energy/export energy" of households. It uses the ZIP pricing strategy within the tariff price range to generate bid/ask prices for the orders, then conducts matching through the Continuous Double Auction (CDA), and finally outputs the transaction results and unmatched orders.

- `main.py`: main entry point
- `cda.py`: CDA market clearing mechanism
- `zip_strategy.py`: ZIP pricing strategy
- `order_book.py`: order book  
- `tariff.py`: ToU and FiT tariff loading
- `committed_trade.py`: output trade and unmatched order formatting
- `test_household.py`: random test household generation

It includes zip_strategy.py, tariff.py and test_household.py for testing.
However, zip_strategy.py will be moved to the household module, tariff.py will be moved to the main grid module, and test_household.py will be removed finally.

Expected input
- `DateTime`
- `h_id`
- `import_energy`
- `export_energy`

 Expected output
 - 'committed_trades': finalized trade records, including buyer ID, seller ID, quantity, trade price, and trade value
 - 'unmatched_orders': remaining unmatched orders after market clearing
 - 'num_trades'
 - 'num_unmatched_orders'
 - 'matched_records'
