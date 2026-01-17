"""
Test für scanner/pipeline/output.py
"""

import sys
sys.path.insert(0, '.')

from scanner.pipeline.output import ReportGenerator
from pathlib import Path

print("=" * 80)
print("TEST: Report Generator")
print("=" * 80)

# Test config
test_config = {
    'output': {
        'reports_dir': 'reports_test',
        'top_n_per_setup': 3
    }
}

# Mock scoring results
mock_reversals = [
    {
        'symbol': 'BESTREV',
        'score': 95.5,
        'components': {'drawdown': 100, 'base': 95, 'reclaim': 90, 'volume': 100},
        'flags': [],
        'reasons': ['Strong drawdown setup (65% from ATH)', 'Clean base formation']
    },
    {
        'symbol': 'GOODREV',
        'score': 75.0,
        'components': {'drawdown': 80, 'base': 70, 'reclaim': 75, 'volume': 70},
        'flags': ['low_liquidity'],
        'reasons': ['Moderate setup', '⚠️ Low liquidity']
    }
]

mock_breakouts = [
    {
        'symbol': 'BESTBO',
        'score': 88.3,
        'components': {'breakout': 90, 'volume': 100, 'trend': 85, 'momentum': 80},
        'flags': [],
        'reasons': ['Strong breakout (7% above high)', 'Strong volume (3x)']
    }
]

mock_pullbacks = [
    {
        'symbol': 'BESTPB',
        'score': 82.0,
        'components': {'trend': 90, 'pullback': 100, 'rebound': 60, 'volume': 80},
        'flags': [],
        'reasons': ['At support level', 'Strong uptrend']
    }
]

# Initialize generator
print("\n--- Initializing Report Generator ---")
generator = ReportGenerator(test_config)
print(f"✓ Generator ready: {generator.reports_dir}")

# Generate reports
print("\n--- Generating Reports ---")
run_date = '2026-01-17'

paths = generator.save_reports(
    reversal_results=mock_reversals,
    breakout_results=mock_breakouts,
    pullback_results=mock_pullbacks,
    run_date=run_date,
    metadata={'test': True}
)

print(f"\n✓ Markdown report: {paths['markdown']}")
print(f"✓ JSON report: {paths['json']}")

# Validate files exist
print("\n--- Validation ---")
success = True

if not paths['markdown'].exists():
    print("❌ Markdown file not created")
    success = False
else:
    print("✓ Markdown file exists")
    
    # Check content
    md_content = paths['markdown'].read_text()
    if 'BESTREV' not in md_content:
        print("❌ Markdown missing BESTREV")
        success = False
    else:
        print("✓ Markdown contains expected symbols")

if not paths['json'].exists():
    print("❌ JSON file not created")
    success = False
else:
    print("✓ JSON file exists")
    
    import json
    json_data = json.loads(paths['json'].read_text())
    
    if json_data['summary']['reversal_count'] != 2:
        print("❌ JSON summary incorrect")
        success = False
    else:
        print("✓ JSON summary correct")

# Show preview
print("\n--- Markdown Preview (first 20 lines) ---")
md_content = paths['markdown'].read_text()
lines = md_content.split('\n')[:20]
for line in lines:
    print(line)

# Final result
if success:
    print("\n✅ TEST PASSED!")
    print(f"\nReports saved in: {generator.reports_dir}/")
else:
    print("\n❌ TEST FAILED!")

print("\n" + "=" * 80)
