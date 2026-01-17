"""
Test für scanner/pipeline/features.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.features import FeatureEngine

print("=" * 80)
print("TEST: FeatureEngine")
print("=" * 80)

# Mock OHLCV data (realistic format)
mock_ohlcv = {
    'BTCUSDT': {
        '1d': [
            # [timestamp, open, high, low, close, volume, ...]
            [1700000000000, 50000, 50500, 49500, 50200, 1000],
            [1700086400000, 50200, 50800, 50000, 50600, 1100],
            [1700172800000, 50600, 51000, 50400, 50900, 1050],
            [1700259200000, 50900, 51500, 50700, 51300, 1200],
            [1700345600000, 51300, 51800, 51100, 51600, 1150],
            [1700432000000, 51600, 52000, 51400, 51800, 1100],
            [1700518400000, 51800, 52200, 51600, 52000, 1250],
            [1700604800000, 52000, 52500, 51800, 52300, 1300],
            [1700691200000, 52300, 52700, 52100, 52500, 1200],
            [1700777600000, 52500, 53000, 52300, 52800, 1350],
            # ... more bars for EMA50
        ] + [[1700000000000 + i*86400000, 50000+i*50, 50500+i*50, 49500+i*50, 50000+i*50, 1000] for i in range(10, 60)],
        '4h': [
            [1700000000000 + i*14400000, 50000+i*10, 50100+i*10, 49900+i*10, 50000+i*10, 200]
            for i in range(100)
        ]
    },
    'ETHUSDT': {
        '1d': [
            [1700000000000 + i*86400000, 3000+i*5, 3010+i*5, 2990+i*5, 3000+i*5, 800]
            for i in range(60)
        ],
        '4h': [
            [1700000000000 + i*14400000, 3000+i*2, 3005+i*2, 2995+i*2, 3000+i*2, 150]
            for i in range(100)
        ]
    }
}

# Initialize engine
print("\n--- Initializing Feature Engine ---")
engine = FeatureEngine(config={})
print("✓ Engine ready")

# Compute features
print("\n--- Computing Features ---")
features = engine.compute_all(mock_ohlcv)

# Results
print("\n--- Results ---")
print(f"Features computed for {len(features)} symbols")

for symbol, feat_data in features.items():
    print(f"\n{symbol}:")
    print(f"  Meta: {feat_data.get('meta', {})}")
    
    if '1d' in feat_data:
        f1d = feat_data['1d']
        print(f"  1d Features:")
        print(f"    close: {f1d.get('close', 0):.2f}")
        
        ema20 = f1d.get('ema_20')
        print(f"    ema_20: {ema20:.2f if ema20 is not None else 'N/A'}")
        
        ema50 = f1d.get('ema_50')
        print(f"    ema_50: {ema50:.2f if ema50 is not None else 'N/A'}")
        
        r7 = f1d.get('r_7')
        print(f"    r_7: {r7:.2f if r7 is not None else 'N/A'}%")
        
        atr = f1d.get('atr_pct')
        print(f"    atr_pct: {atr:.2f if atr is not None else 'N/A'}%")
        
        vol_spike = f1d.get('volume_spike')
        print(f"    volume_spike: {vol_spike:.2f if vol_spike is not None else 'N/A'}x")
        
        dd = f1d.get('drawdown_from_ath')
        print(f"    drawdown_from_ath: {dd:.2f if dd is not None else 'N/A'}%")
        
        print(f"    hh_20: {f1d.get('hh_20')}")
        print(f"    base_detected: {f1d.get('base_detected')}")
    
    if '4h' in feat_data:
        f4h = feat_data['4h']
        print(f"  4h Features:")
        print(f"    close: {f4h.get('close', 0):.2f}")
        
        ema20 = f4h.get('ema_20')
        print(f"    ema_20: {ema20:.2f if ema20 is not None else 'N/A'}")
        
        vol_spike = f4h.get('volume_spike')
        print(f"    volume_spike: {vol_spike:.2f if vol_spike is not None else 'N/A'}x")

# Validation
print("\n--- Validation ---")
success = True

required_features_1d = ['close', 'ema_20', 'ema_50', 'r_7', 'atr_pct', 'volume_spike', 'drawdown_from_ath']
required_features_4h = ['close', 'ema_20', 'volume_spike']

for symbol in features:
    # Check 1d features
    if '1d' in features[symbol]:
        for feat in required_features_1d:
            if feat not in features[symbol]['1d']:
                print(f"❌ {symbol} 1d: Missing feature '{feat}'")
                success = False
    
    # Check 4h features
    if '4h' in features[symbol]:
        for feat in required_features_4h:
            if feat not in features[symbol]['4h']:
                print(f"❌ {symbol} 4h: Missing feature '{feat}'")
                success = False

if success:
    print("✓ All required features present")

# Final result
if success:
    print("\n✅ TEST PASSED!")
else:
    print("\n❌ TEST FAILED!")

print("\n" + "=" * 80)
