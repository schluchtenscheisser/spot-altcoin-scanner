"""
Pipeline Orchestration
======================

Orchestrates the full daily scanning pipeline.
"""

from __future__ import annotations
import logging
from ..utils.time_utils import utc_now, timestamp_to_ms

from ..config import ScannerConfig
from ..clients.mexc_client import MEXCClient
from ..clients.marketcap_client import MarketCapClient
from ..clients.mapping import SymbolMapper
from .filters import UniverseFilters
from .shortlist import ShortlistSelector
from .ohlcv import OHLCVFetcher
from .features import FeatureEngine
from .scoring.reversal import score_reversals
from .scoring.breakout import score_breakouts
from .scoring.pullback import score_pullbacks
from .output import ReportGenerator
from .global_ranking import compute_global_top20
from .liquidity import fetch_orderbooks_for_top_k, apply_liquidity_metrics_to_shortlist
from .snapshot import SnapshotManager
from .runtime_market_meta import RuntimeMarketMetaExporter
from .discovery import compute_discovery_fields
from .regime import compute_btc_regime

logger = logging.getLogger(__name__)


def run_pipeline(config: ScannerConfig) -> None:
    """
    Orchestrates the full daily pipeline:
    1. Fetch universe (MEXC Spot USDT)
    2. Fetch market cap listings
    3. Run mapping layer
    4. Apply hard filters (market cap, liquidity, exclusions)
    5. Run cheap pass (shortlist)
    6. Liquidity stage: orderbook fetch for Top-K only
    7. Fetch OHLCV for shortlist
    8. Compute features (1d + 4h)
    9. Enrich features with price, name, market cap, and volume
    10. Compute scores (breakout / pullback / reversal)
    11. Write reports (Markdown + JSON + Excel)
    12. Write snapshot for backtests
    """
    run_mode = config.run_mode

    # As-Of Timestamp (einmal pro Run)
    asof_dt = utc_now()
    asof_ts_ms = timestamp_to_ms(asof_dt)
    asof_iso = asof_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Run-Date konsistent aus asof_dt
    run_date = asof_dt.strftime('%Y-%m-%d')
    
    use_cache = run_mode in ['fast', 'standard']
    
    logger.info("=" * 80)
    logger.info(f"PIPELINE STARTING - {run_date}")
    logger.info(f"Mode: {run_mode}")
    logger.info("=" * 80)
    
    # Initialize clients
    logger.info("\n[INIT] Initializing clients...")
    mexc = MEXCClient()
    cmc = MarketCapClient(api_key=config.cmc_api_key)
    logger.info("✓ Clients initialized")
    
    # Step 1: Fetch universe (MEXC Spot USDT)
    logger.info("\n[1/12] Fetching MEXC universe...")
    exchange_info_ts_utc = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    exchange_info = mexc.get_exchange_info(use_cache=use_cache)

    universe = []
    for symbol_info in exchange_info.get("symbols", []):
        if (
            symbol_info.get("quoteAsset") == "USDT"
            and symbol_info.get("isSpotTradingAllowed", False)
            and symbol_info.get("status") == "1"
        ):
            universe.append(symbol_info["symbol"])

    logger.info(f"✓ Universe: {len(universe)} USDT pairs")
    
    # Get 24h tickers
    logger.info("  Fetching 24h tickers...")
    tickers_24h_ts_utc = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    tickers = mexc.get_24h_tickers(use_cache=use_cache)
    ticker_map = {t['symbol']: t for t in tickers}
    logger.info(f"  ✓ Tickers: {len(ticker_map)} symbols")
    
    # Step 2 & 3: Fetch market cap + Run mapping layer
    logger.info("\n[2-3/12] Fetching market cap & mapping...")
    cmc_listings_ts_utc = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    cmc_listings = cmc.get_listings(use_cache=use_cache)
    cmc_symbol_map = cmc.build_symbol_map(cmc_listings)
    logger.info(f"  ✓ CMC: {len(cmc_symbol_map)} symbols")
    
    mapper = SymbolMapper()
    mapping_results = mapper.map_universe(universe, cmc_symbol_map)
    logger.info(f"✓ Mapped: {mapper.stats['mapped']}/{mapper.stats['total']} "
               f"({mapper.stats['mapped']/mapper.stats['total']*100:.1f}%)")
    
    # Prepare data for filters
    symbols_with_data = []
    for symbol in universe:
        result = mapping_results.get(symbol)
        if not result or not result.mapped:
            continue
        
        ticker = ticker_map.get(symbol, {})
        
        symbols_with_data.append({
            'symbol': symbol,
            'base': symbol.replace('USDT', ''),
            'quote_volume_24h': float(ticker.get('quoteVolume', 0)),
            'market_cap': result._get_market_cap()
        })
    
    # Step 4: Apply hard filters
    logger.info("\n[4/12] Applying universe filters...")
    filters = UniverseFilters(config.raw)
    filtered = filters.apply_all(symbols_with_data)
    logger.info(f"✓ Filtered: {len(filtered)} symbols")
    
    # Step 5: Run cheap pass (shortlist)
    logger.info("\n[5/12] Creating shortlist...")
    selector = ShortlistSelector(config.raw)
    shortlist = selector.select(filtered)
    logger.info(f"✓ Shortlist: {len(shortlist)} symbols")
    
    # Step 6: Liquidity Stage (Top-K orderbook budget)
    logger.info("\n[6/12] Liquidity stage: fetching orderbook for Top-K only...")
    orderbooks = fetch_orderbooks_for_top_k(mexc, shortlist, config.raw)
    logger.info(f"✓ Orderbooks fetched: {len(orderbooks)} (Top-K budget)")
    shortlist = apply_liquidity_metrics_to_shortlist(shortlist, orderbooks, config.raw)

    # Hard Exclude: liquidity grade D must not enter downstream scoring universe
    before_liquidity_gate = len(shortlist)
    shortlist = [s for s in shortlist if str(s.get('liquidity_grade') or '').upper() != 'D']
    if len(shortlist) != before_liquidity_gate:
        logger.info(
            "  Liquidity hard gate removed %s symbols with liquidity_grade=D",
            before_liquidity_gate - len(shortlist),
        )

    # Step 7: Fetch OHLCV for shortlist
    logger.info("\n[7/12] Fetching OHLCV data...")
    ohlcv_fetcher = OHLCVFetcher(mexc, config.raw)
    ohlcv_data = ohlcv_fetcher.fetch_all(shortlist)
    logger.info(f"✓ OHLCV: {len(ohlcv_data)} symbols with complete data")
    
    # Step 8: Compute features (1d + 4h)
    logger.info("\n[8/12] Computing features...")
    feature_engine = FeatureEngine(config.raw)
    features = feature_engine.compute_all(ohlcv_data, asof_ts_ms=asof_ts_ms)
    logger.info(f"✓ Features: {len(features)} symbols")

    logger.info("  Computing BTC regime...")
    btc_regime = compute_btc_regime(
        mexc_client=mexc,
        feature_engine=feature_engine,
        lookback_1d=ohlcv_fetcher.lookback.get("1d", 120),
        asof_ts_ms=asof_ts_ms,
    )
    logger.info("  ✓ BTC regime: %s", btc_regime.get("state"))

    # Step 9: Enrich features with price, coin name, market cap, and volume
    logger.info("\n[9/12] Enriching features with price, name, market cap, and volume...")
    for symbol in features.keys():
        # Add current price from tickers
        ticker = ticker_map.get(symbol)
        if ticker:
            features[symbol]['price_usdt'] = float(ticker.get('lastPrice', 0))
        else:
            features[symbol]['price_usdt'] = None
    
        # Add coin name from CMC
        mapping = mapper.map_symbol(symbol, cmc_symbol_map)
        if mapping.mapped and mapping.cmc_data:
            features[symbol]['coin_name'] = mapping.cmc_data.get('name', 'Unknown')
            features[symbol]['cmc_date_added'] = mapping.cmc_data.get('date_added')
        else:
            features[symbol]['coin_name'] = 'Unknown'
            features[symbol]['cmc_date_added'] = None
        
        # Add market cap and volume from shortlist data
        shortlist_entry = next((s for s in shortlist if s['symbol'] == symbol), None)
        if shortlist_entry:
            features[symbol]['market_cap'] = shortlist_entry.get('market_cap')
            features[symbol]['quote_volume_24h'] = shortlist_entry.get('quote_volume_24h')
            features[symbol]['proxy_liquidity_score'] = shortlist_entry.get('proxy_liquidity_score')
            features[symbol]['spread_bps'] = shortlist_entry.get('spread_bps')
            features[symbol]['slippage_bps'] = shortlist_entry.get('slippage_bps')
            features[symbol]['liquidity_grade'] = shortlist_entry.get('liquidity_grade')
            features[symbol]['liquidity_insufficient'] = shortlist_entry.get('liquidity_insufficient')
            features[symbol]['risk_flags'] = shortlist_entry.get('risk_flags', [])
            features[symbol]['soft_penalties'] = shortlist_entry.get('soft_penalties', {})
        else:
            features[symbol]['market_cap'] = None
            features[symbol]['quote_volume_24h'] = None
            features[symbol]['proxy_liquidity_score'] = None
            features[symbol]['spread_bps'] = None
            features[symbol]['slippage_bps'] = None
            features[symbol]['liquidity_grade'] = None
            features[symbol]['liquidity_insufficient'] = None
            features[symbol]['risk_flags'] = []
            features[symbol]['soft_penalties'] = {}

        symbol_ohlcv = ohlcv_data.get(symbol, {})
        first_seen_ts = None
        if isinstance(symbol_ohlcv, dict) and symbol_ohlcv.get('1d'):
            first = symbol_ohlcv['1d'][0]
            if isinstance(first, (list, tuple)) and first:
                try:
                    first_seen_ts = int(float(first[0]))
                except (TypeError, ValueError):
                    first_seen_ts = None

        discovery_cfg = config.raw.get('discovery', {}) if isinstance(config.raw, dict) else {}
        discovery_fields = compute_discovery_fields(
            asof_ts_ms=asof_ts_ms,
            date_added=features[symbol].get('cmc_date_added'),
            first_seen_ts=first_seen_ts,
            max_age_days=int(discovery_cfg.get('max_age_days', 180)),
        )
        features[symbol]['first_seen_ts'] = first_seen_ts
        features[symbol].update(discovery_fields)

    logger.info(f"✓ Enriched {len(features)} symbols with price, name, market cap, and volume")
    
    # Prepare volume map for scoring (backwards compatibility)
    volume_map = {s['symbol']: s['quote_volume_24h'] for s in shortlist}
    
    # Step 10: Compute scores (breakout / pullback / reversal)
    logger.info("\n[10/12] Scoring setups...")
    
    logger.info("  Scoring Reversals...")
    reversal_results = score_reversals(features, volume_map, config.raw)
    logger.info(f"  ✓ Reversals: {len(reversal_results)} scored")
    
    logger.info("  Scoring Breakouts...")
    breakout_results = score_breakouts(features, volume_map, config.raw)
    logger.info(f"  ✓ Breakouts: {len(breakout_results)} scored")
    
    logger.info("  Scoring Pullbacks...")
    pullback_results = score_pullbacks(features, volume_map, config.raw)
    logger.info(f"  ✓ Pullbacks: {len(pullback_results)} scored")

    global_top20 = compute_global_top20(
        reversal_results=reversal_results,
        breakout_results=breakout_results,
        pullback_results=pullback_results,
        config=config.raw,
    )
    logger.info(f"  ✓ Global Top20: {len(global_top20)} entries")
    
    # Step 11: Write reports (Markdown + JSON + Excel)
    logger.info("\n[11/12] Generating reports...")
    report_gen = ReportGenerator(config.raw)
    report_paths = report_gen.save_reports(
        reversal_results,
        breakout_results,
        pullback_results,
        global_top20,
        run_date,
        metadata={
            'mode': run_mode,
            'asof_ts_ms': asof_ts_ms,
            'asof_iso': asof_iso,
        },
        btc_regime=btc_regime,
    )
    logger.info(f"✓ Markdown: {report_paths['markdown']}")
    logger.info(f"✓ JSON: {report_paths['json']}")
    if 'excel' in report_paths:
        logger.info(f"✓ Excel: {report_paths['excel']}")
    
    # Step 12: Write snapshot for backtests
    logger.info("\n[12/12] Creating snapshot...")
    snapshot_mgr = SnapshotManager(config.raw)
    snapshot_path = snapshot_mgr.create_snapshot(
        run_date=run_date,
        universe=[{'symbol': s} for s in universe],
        filtered=filtered,
        shortlist=shortlist,
        features=features,
        reversal_scores=reversal_results,
        breakout_scores=breakout_results,
        pullback_scores=pullback_results,
        metadata={
            'mode': run_mode,
            'asof_ts_ms': asof_ts_ms,
            'asof_iso': asof_iso,
        }
    )
    logger.info(f"✓ Snapshot: {snapshot_path}")

    runtime_meta_exporter = RuntimeMarketMetaExporter(config)
    runtime_meta_path = runtime_meta_exporter.export(
        run_date=run_date,
        asof_iso=asof_iso,
        run_id=str(asof_ts_ms),
        filtered_symbols=[entry['symbol'] for entry in filtered],
        mapping_results=mapping_results,
        exchange_info=exchange_info,
        ticker_map=ticker_map,
        features=features,
        ohlcv_data=ohlcv_data,
        exchange_info_ts_utc=exchange_info_ts_utc,
        tickers_24h_ts_utc=tickers_24h_ts_utc,
        listings_ts_utc=cmc_listings_ts_utc,
    )
    logger.info(f"✓ Runtime Market Meta: {runtime_meta_path}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Date: {run_date}")
    logger.info(f"Universe: {len(universe)} symbols")
    logger.info(f"Filtered: {len(filtered)} symbols")
    logger.info(f"Shortlist: {len(shortlist)} symbols")
    logger.info(f"Features: {len(features)} symbols")
    logger.info(f"\nScored:")
    logger.info(f"  Reversals: {len(reversal_results)}")
    logger.info(f"  Breakouts: {len(breakout_results)}")
    logger.info(f"  Pullbacks: {len(pullback_results)}")
    logger.info(f"\nOutputs:")
    logger.info(f"  Report: {report_paths['markdown']}")
    if 'excel' in report_paths:
        logger.info(f"  Excel: {report_paths['excel']}")
    logger.info(f"  Snapshot: {snapshot_path}")
    logger.info(f"  Runtime Market Meta: {runtime_meta_path}")
    logger.info("=" * 80)
