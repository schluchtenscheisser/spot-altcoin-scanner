"""
Test für scanner/pipeline/scoring/reversal.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.scoring.reversal import ReversalScorer, score_reversals

print("=" * 80)
print("TEST: Reversal Scorer")
print("=" * 80)

# Test config
test_config = {
    'scoring': {
        'reversal': {
            'min_drawdown_pct': 40,
            'ideal_drawdown_min': 50,
            'ideal_drawdown_max': 80,
            'min_volume_spike': 1.5,
            'overextension_threshold': 15
        }
    }
}

# Mock features (Humanity Protocol style setup)
mock_features = {
    'GOODUSDT': {  # Perfect reversal setup
        '1d': {
            'close': 1.5,
            'drawdown_from_ath': -65,  # 65% drawdown (ideal range)
            'base_detected': True,
            'atr_pct': 4.5,  # Tight base
            'dist_ema20_pct': 5.0,  # Above EMA20
            'dist_ema50_pct': 3.0,  # Above EMA50
            'hh_20': True,
            'r_7': 12.0,  # Strong momentum
            'volume_spike': 2.5  # Strong volume
        },
        '4h': {
            'volume_spike': 2.8
        }
    },
    'EARLYUSDT': {  # Too early (still declining)
        '1d': {
            'close': 0.8,
            'drawdown_from_ath': -55,
            'base_detected': False,  # No base yet
            'atr_pct': 12.0,  # High volatility
            'dist_ema20_pct': -10.0,  # Below EMAs
            'dist_ema50_pct': -15.0,
            'hh_20': False,
            'r_7': -5.0,
            'volume_spike': 1.0
        },
        '4h': {
            'volume_spike': 1.1
        }
    },
    'LATEUSDT': {  # Too late (overextended)
        '1d': {
            'close': 2.5,
            'drawdown_from_ath': -30,  # Small drawdown
            'base_detected': True,
            'atr_pct': 8.0,
            'dist_ema20_pct': 25.0,  # Way above
            'dist_ema50_pct': 20.0,  # Overextended!
            'hh_20': True,
            'r_7': 35.0,
            'volume_spike': 1.2
        },
        '4h': {
            'volume_spike': 1.3
        }
    }
}

# Mock volumes
mock_volumes = {
    'GOODUSDT': 2_000_000,  # Good liquidity
    'EARLYUSDT': 1_500_000,
    'LATEUSDT': 300_000  # Low liquidity
}

print("\n--- Initializing Reversal Scorer ---")
scorer = ReversalScorer(test_config)
print("✓ Scorer ready")

print("\n--- Scoring Individual Symbols ---")
for symbol, features in mock_features.items():
    volume = mock_volumes.get(symbol, 0)
    result = scorer.score(symbol, features, volume)
    
    print(f"\n{symbol}:")
    print(f"  Score: {result['score']:.2f}")
    print(f"  Components:")
    for comp, val in result['components'].items():
        print(f"    {comp}: {val:.2f}")
    
    if result['penalties']:
        print(f"  Penalties:")
        for pen, factor in result['penalties'].items():
            print(f"    {pen}: {factor:.2f}x")
    
    if result['flags']:
        print(f"  Flags: {', '.join(result['flags'])}")
    
    print(f"  Reasons:")
    for reason in result['reasons']:
        print(f"    - {reason}")

print("\n--- Batch Scoring & Ranking ---")
ranked = score_reversals(mock_features, mock_volumes, test_config)

print(f"\nRanked List (Top {len(ranked)}):")
for i, entry in enumerate(ranked, 1):
    print(f"{i}. {entry['symbol']}: {entry['score']:.2f}")

# Validation
print("\n--- Validation ---")
success = True

# GOODUSDT should score highest
if ranked[0]['symbol'] != 'GOODUSDT':
    print("❌ GOODUSDT should rank first (best setup)")
    success = False
else:
    print("✓ GOODUSDT ranks first (correct)")

# EARLYUSDT should have low score (no base)
early_result = next(r for r in ranked if r['symbol'] == 'EARLYUSDT')
if early_result['score'] > 30:
    print(f"❌ EARLYUSDT score too high ({early_result['score']:.2f}, should be <30)")
    success = False
else:
    print(f"✓ EARLYUSDT has low score ({early_result['score']:.2f})")

# LATEUSDT should have penalties
late_result = next(r for r in ranked if r['symbol'] == 'LATEUSDT')
if 'overextended' not in late_result['flags']:
    print("❌ LATEUSDT should be flagged as overextended")
    success = False
else:
    print("✓ LATEUSDT flagged as overextended")

if success:
    print("\n✅ TEST PASSED!")
else:
    print("\n❌ TEST FAILED!")

print("\n" + "=" * 80)
