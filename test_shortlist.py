"""
Test für scanner/pipeline/shortlist.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.shortlist import ShortlistSelector

# Test-Config
test_config = {
    'shortlist': {
        'max_size': 3,  # Small for testing
        'min_size': 1
    }
}

# Test-Daten (bereits gefiltert, verschiedene Volumes)
test_symbols = [
    {
        'symbol': 'BTCUSDT',
        'base': 'BTC',
        'quote_volume_24h': 10_000_000,  # Highest
        'market_cap': 500_000_000
    },
    {
        'symbol': 'ETHUSDT',
        'base': 'ETH',
        'quote_volume_24h': 8_000_000,  # 2nd
        'market_cap': 1_000_000_000
    },
    {
        'symbol': 'SOLUSDT',
        'base': 'SOL',
        'quote_volume_24h': 5_000_000,  # 3rd
        'market_cap': 1_500_000_000
    },
    {
        'symbol': 'ADAUSDT',
        'base': 'ADA',
        'quote_volume_24h': 3_000_000,  # Should be cut (4th)
        'market_cap': 800_000_000
    },
    {
        'symbol': 'DOTUSDT',
        'base': 'DOT',
        'quote_volume_24h': 1_000_000,  # Should be cut (5th)
        'market_cap': 600_000_000
    }
]

print("=" * 80)
print("TEST: ShortlistSelector")
print("=" * 80)

# Initialize selector
selector = ShortlistSelector(test_config)

print("\n--- INPUT (Filtered Universe) ---")
print(f"Total symbols: {len(test_symbols)}")
for s in test_symbols:
    print(f"  {s['symbol']}: VOL=${s['quote_volume_24h']/1e6:.2f}M, MCAP=${s['market_cap']/1e6:.0f}M")

print("\n--- SELECTING SHORTLIST (Top 3 by Volume) ---")
shortlist = selector.select(test_symbols)

print("\n--- OUTPUT (Shortlist) ---")
print(f"Shortlist size: {len(shortlist)}")
for s in shortlist:
    print(f"  ✓ {s['symbol']}: VOL=${s['quote_volume_24h']/1e6:.2f}M")

print("\n--- STATISTICS ---")
stats = selector.get_shortlist_stats(test_symbols, shortlist)
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n--- VALIDATION ---")
expected_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
actual_symbols = [s['symbol'] for s in shortlist]

print(f"Expected (top 3): {expected_symbols}")
print(f"Actual:           {actual_symbols}")

# Check order (should be volume-descending)
volumes = [s['quote_volume_24h'] for s in shortlist]
is_sorted = volumes == sorted(volumes, reverse=True)

if actual_symbols == expected_symbols and is_sorted:
    print("\n✅ TEST PASSED!")
    print("   - Correct symbols selected")
    print("   - Correct order (volume descending)")
else:
    print("\n❌ TEST FAILED!")
    if actual_symbols != expected_symbols:
        print(f"   - Wrong symbols: {set(expected_symbols) - set(actual_symbols)}")
    if not is_sorted:
        print(f"   - Wrong order: {volumes} (should be descending)")

print("\n" + "=" * 80)
