"""
Test für scanner/pipeline/scoring/breakout.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.scoring.breakout import BreakoutScorer, score_breakouts

print("=" * 80)
print("TEST: Breakout Scorer")
print("=" * 80)

# Test config
test_config = {
    'scoring': {
        'breakout': {
            'min_breakout_pct': 2,
            'ideal_breakout_pct': 5,
            'max_breakout_pct': 20,
            'min_volume_spike': 1.5,
            'ideal_volume_spike': 2.5
        }
    }
}

# Mock features
mock_features = {
    'PERFECTBO': {  # Perfect breakout
        '1d': {
            'close': 1.0,
            'breakout_dist_20': 7.0,  # 7% above high (ideal)
            'dist_ema20_pct': 8.0,  # Above EMAs
            'dist_ema50_pct': 5.0,
            'r_7': 15.0,  # Strong momentum
            'volume_spike': 3.0  # Strong volume
        },
        '4h': {
            'volume_spike': 2.8
        }
    },
    'EARLYBO': {  # Early/weak breakout
        '1d': {
            'close': 1.0,
            'breakout_dist_20': 2.5,  # Just above high
            'dist_ema20_pct': 1.0,
            'dist_ema50_pct': -2.0,  # Below EMA50
            'r_7': 3.0,  # Weak momentum
            'volume_spike': 1.3  # Low volume
        },
        '4h': {
            'volume_spike': 1.4
        }
    },
    'OVEREXTBO': {  # Overextended breakout
        '1d': {
            'close': 1.0,
            'breakout_dist_20': 25.0,  # 25% above (too much!)
            'dist_ema20_pct': 30.0,
            'dist_ema50_pct': 28.0,
            'r_7': 40.0,
            'volume_spike': 1.8
        },
        '4h': {
            'volume_spike': 2.0
        }
    }
}

mock_volumes = {
    'PERFECTBO': 2_000_000,
    'EARLYBO': 1_500_000,
    'OVEREXTBO': 800_000
}

print("\n--- Initializing Breakout Scorer ---")
scorer = BreakoutScorer(test_config)
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
ranked = score_breakouts(mock_features, mock_volumes, test_config)

print(f"\nRanked List:")
for i, entry in enumerate(ranked, 1):
    print(f"{i}. {entry['symbol']}: {entry['score']:.2f}")

# Validation
print("\n--- Validation ---")
success = True

# PERFECTBO should rank first
if ranked[0]['symbol'] != 'PERFECTBO':
    print("❌ PERFECTBO should rank first")
    success = False
else:
    print("✓ PERFECTBO ranks first")

# OVEREXTBO should be flagged
overext = next(r for r in ranked if r['symbol'] == 'OVEREXTBO')
if 'overextended' not in overext['flags']:
    print("❌ OVEREXTBO should be flagged as overextended")
    success = False
else:
    print("✓ OVEREXTBO flagged as overextended")

# EARLYBO should have low score
early = next(r for r in ranked if r['symbol'] == 'EARLYBO')
if early['score'] > 50:
    print(f"❌ EARLYBO score too high ({early['score']:.2f})")
    success = False
else:
    print(f"✓ EARLYBO has low score ({early['score']:.2f})")

if success:
    print("\n✅ TEST PASSED!")
else:
    print("\n❌ TEST FAILED!")

print("\n" + "=" * 80)
