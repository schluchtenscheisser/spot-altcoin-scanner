from scanner.clients.mexc_client import MEXCClient
from scanner.clients.marketcap_client import MarketCapClient
from scanner.clients.mapping import SymbolMapper

# Step 1: Get MEXC universe
print("=" * 60)
print("STEP 1: Loading MEXC Universe")
print("=" * 60)
mexc = MEXCClient()
mexc_symbols = mexc.get_spot_usdt_symbols()
print(f"✅ Found {len(mexc_symbols)} MEXC USDT pairs")
print(f"   Examples: {mexc_symbols[:5]}")

# Step 2: Get CMC data
print("\n" + "=" * 60)
print("STEP 2: Loading CMC Data")
print("=" * 60)
cmc = MarketCapClient()
cmc_listings = cmc.get_all_listings()
cmc_symbol_map = cmc.build_symbol_map(cmc_listings)
print(f"✅ CMC data: {len(cmc_symbol_map)} unique symbols")

# Step 3: Map universe
print("\n" + "=" * 60)
print("STEP 3: Mapping MEXC → CMC")
print("=" * 60)
mapper = SymbolMapper()
mapping_results = mapper.map_universe(mexc_symbols, cmc_symbol_map)

# Step 4: Show stats
print("\n" + "=" * 60)
print("MAPPING RESULTS")
print("=" * 60)
print(f"Total symbols: {mapper.stats['total']}")
print(f"Mapped: {mapper.stats['mapped']} ({mapper.stats['mapped']/mapper.stats['total']*100:.1f}%)")
print(f"Unmapped: {mapper.stats['unmapped']}")
print(f"Confidence breakdown:")
for level, count in mapper.stats['confidence'].items():
    print(f"  {level}: {count}")

# Step 5: Show examples
print("\n" + "=" * 60)
print("EXAMPLES")
print("=" * 60)

# Mapped examples
mapped = [r for r in mapping_results.values() if r.mapped][:3]
print("Mapped:")
for r in mapped:
    mcap = r._get_market_cap()
    print(f"  {r.mexc_symbol} → {r.cmc_data['name']} (${mcap:,.0f})")

# Unmapped examples
unmapped = [r for r in mapping_results.values() if not r.mapped][:3]
print("\nUnmapped:")
for r in unmapped:
    print(f"  {r.mexc_symbol} ({r.base_asset}) - {r.notes}")

# Step 6: Generate reports
print("\n" + "=" * 60)
print("GENERATING REPORTS")
print("=" * 60)
mapper.generate_reports(mapping_results)
mapper.suggest_overrides(mapping_results)

print("\n🎉 Mapping Layer complete!")
print(f"📊 Check reports/ folder for details")
