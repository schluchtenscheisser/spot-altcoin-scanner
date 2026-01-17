"""
Test für scanner/pipeline/ohlcv.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.ohlcv import OHLCVFetcher
from scanner.clients.mexc_client import MEXCClient
from scanner.config import load_config

print("=" * 80)
print("TEST: OHLCVFetcher")
print("=" * 80)

# Load config
print("\n--- Loading Config ---")
config = load_config()
print("✓ Config loaded")

# Initialize MEXC client
print("\n--- Initializing MEXC Client ---")
mexc = MEXCClient(config)
print("✓ MEXC client ready")

# Test config (override for faster testing)
test_ohlcv_config = {
    'ohlcv': {
        'timeframes': ['1d', '4h'],
        'lookback': {
            '1d': 90,   # 3 months
            '4h': 120   # ~20 days
        },
        'min_candles': {
            '1d': 60,
            '4h': 90
        }
    }
}

# Initialize fetcher
print("\n--- Initializing OHLCV Fetcher ---")
fetcher = OHLCVFetcher(mexc, test_ohlcv_config)
print(f"✓ Fetcher ready: {fetcher.timeframes}")

# Test with small shortlist
print("\n--- Test Shortlist (3 symbols) ---")
test_shortlist = [
    {'symbol': 'BTCUSDT', 'base': 'BTC'},
    {'symbol': 'ETHUSDT', 'base': 'ETH'},
    {'symbol': 'SOLUSDT', 'base': 'SOL'}
]

for s in test_shortlist:
    print(f"  {s['symbol']}")

# Fetch OHLCV
print("\n--- Fetching OHLCV Data ---")
ohlcv_data = fetcher.fetch_all(test_shortlist)

# Results
print("\n--- Results ---")
print(f"Symbols with complete data: {len(ohlcv_data)}/{len(test_shortlist)}")

for symbol, data in ohlcv_data.items():
    print(f"\n{symbol}:")
    for tf, candles in data.items():
        if candles:
            first_time = candles[0][0]
            last_time = candles[-1][0]
            first_close = candles[0][4]
            last_close = candles[-1][4]
            print(f"  {tf}: {len(candles)} candles, "
                  f"Close: {first_close} → {last_close}")

# Statistics
print("\n--- Statistics ---")
stats = fetcher.get_fetch_stats(ohlcv_data)
for key, value in stats.items():
    print(f"  {key}: {value}")

# Validation
print("\n--- Validation ---")
success = True

# Check all symbols present
if len(ohlcv_data) != len(test_shortlist):
    print("❌ Not all symbols fetched successfully")
    success = False
else:
    print("✓ All symbols fetched")

# Check timeframes
for symbol in test_shortlist:
    sym = symbol['symbol']
    if sym not in ohlcv_data:
        continue
    
    for tf in fetcher.timeframes:
        if tf not in ohlcv_data[sym]:
            print(f"❌ {sym}: Missing timeframe {tf}")
            success = False
        elif len(ohlcv_data[sym][tf]) < fetcher.min_candles.get(tf, 60):
            print(f"❌ {sym} {tf}: Too few candles ({len(ohlcv_data[sym][tf])})")
            success = False

if success:
    print("✓ All timeframes present with sufficient data")

# Final result
if success:
    print("\n✅ TEST PASSED!")
else:
    print("\n❌ TEST FAILED!")

print("\n" + "=" * 80)
