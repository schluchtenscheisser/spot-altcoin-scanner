"""
Test für scanner/pipeline/snapshot.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.snapshot import SnapshotManager

print("=" * 80)
print("TEST: Snapshot Manager")
print("=" * 80)

# Test config
test_config = {
    'snapshots': {
        'runtime_dir': 'snapshots_test/runtime'
    }
}

# Mock pipeline data
mock_universe = [
    {'symbol': 'BTCUSDT', 'base': 'BTC'},
    {'symbol': 'ETHUSDT', 'base': 'ETH'},
    {'symbol': 'SOLUSDT', 'base': 'SOL'}
]

mock_filtered = [
    {'symbol': 'BTCUSDT', 'base': 'BTC', 'market_cap': 500_000_000},
    {'symbol': 'SOLUSDT', 'base': 'SOL', 'market_cap': 1_500_000_000}
]

mock_shortlist = [
    {'symbol': 'BTCUSDT', 'base': 'BTC'}
]

mock_features = {
    'BTCUSDT': {
        '1d': {'close': 50000, 'ema_20': 49000},
        '4h': {'close': 50100, 'ema_20': 49500}
    }
}

mock_reversals = [
    {'symbol': 'BTCUSDT', 'score': 85.0}
]

mock_breakouts = [
    {'symbol': 'BTCUSDT', 'score': 75.0}
]

mock_pullbacks = [
    {'symbol': 'BTCUSDT', 'score': 65.0}
]

# Initialize manager
print("\n--- Initializing Snapshot Manager ---")
manager = SnapshotManager(test_config)
print(f"✓ Manager ready: {manager.snapshots_dir}")

# Create snapshot
print("\n--- Creating Snapshot ---")
run_date = '2026-01-17'

snapshot_path = manager.create_snapshot(
    run_date=run_date,
    universe=mock_universe,
    filtered=mock_filtered,
    shortlist=mock_shortlist,
    features=mock_features,
    reversal_scores=mock_reversals,
    breakout_scores=mock_breakouts,
    pullback_scores=mock_pullbacks,
    metadata={'test_run': True}
)

print(f"✓ Snapshot created: {snapshot_path}")

# Load snapshot
print("\n--- Loading Snapshot ---")
loaded = manager.load_snapshot(run_date)
print(f"✓ Snapshot loaded")
print(f"  Universe count: {loaded['pipeline']['universe_count']}")
print(f"  Filtered count: {loaded['pipeline']['filtered_count']}")
print(f"  Shortlist count: {loaded['pipeline']['shortlist_count']}")

# Get stats
print("\n--- Snapshot Stats ---")
stats = manager.get_snapshot_stats(run_date)
for key, value in stats.items():
    print(f"  {key}: {value}")

# List snapshots
print("\n--- Available Snapshots ---")
snapshots = manager.list_snapshots()
print(f"Found {len(snapshots)} snapshot(s):")
for snap in snapshots:
    print(f"  - {snap}")

# Validation
print("\n--- Validation ---")
success = True

if not snapshot_path.exists():
    print("❌ Snapshot file not created")
    success = False
else:
    print("✓ Snapshot file exists")

if loaded['pipeline']['universe_count'] != 3:
    print("❌ Universe count mismatch")
    success = False
else:
    print("✓ Universe count correct")

if loaded['data']['features']['BTCUSDT']['1d']['close'] != 50000:
    print("❌ Features data mismatch")
    success = False
else:
    print("✓ Features data correct")

if stats['reversal_count'] != 1:
    print("❌ Reversal count mismatch")
    success = False
else:
    print("✓ Scoring data correct")

if success:
    print("\n✅ TEST PASSED!")
else:
    print("\n❌ TEST FAILED!")

print("\n" + "=" * 80)
