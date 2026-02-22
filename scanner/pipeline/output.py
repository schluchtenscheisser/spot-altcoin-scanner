"""
Output & Report Generation
===========================

Generates human-readable (Markdown), machine-readable (JSON), and Excel reports
from scored results.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import json

from scanner.schema import REPORT_META_VERSION, REPORT_SCHEMA_VERSION

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates daily reports from scoring results."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            config: Config dict with 'output' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            output_config = config.raw.get('output', {})
        else:
            output_config = config.get('output', {})
        
        self.reports_dir = Path(output_config.get('reports_dir', 'reports'))
        self.top_n = output_config.get('top_n_per_setup', 10)
        
        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Report Generator initialized: reports_dir={self.reports_dir}")
    
    def generate_markdown_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        btc_regime: Dict[str, Any] = None,
    ) -> str:
        """
        Generate Markdown report.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
        
        Returns:
            Markdown content as string
        """
        lines = []
        
        # Header
        lines.append(f"# Spot Altcoin Scanner Report")
        lines.append(f"**Date:** {run_date}")
        lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        btc_regime = btc_regime or {}
        btc_checks = btc_regime.get("checks") or {}
        lines.append("## BTC Regime")
        lines.append("")
        lines.append(f"- **State:** {btc_regime.get('state', 'RISK_OFF')}")
        lines.append(f"- **Multiplier (Risk-On):** {float(btc_regime.get('multiplier_risk_on', 1.0)):.2f}")
        lines.append(f"- **Multiplier (Risk-Off):** {float(btc_regime.get('multiplier_risk_off', 0.85)):.2f}")
        lines.append(f"- **Checks:** close>ema50={bool(btc_checks.get('close_gt_ema50', False))}, ema20>ema50={bool(btc_checks.get('ema20_gt_ema50', False))}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Reversal Setups:** {len(reversal_results)} scored")
        lines.append(f"- **Breakout Setups:** {len(breakout_results)} scored")
        lines.append(f"- **Pullback Setups:** {len(pullback_results)} scored")
        lines.append(f"- **Global Top 20:** {len(global_top20)} ranked")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Global Top 20
        lines.append("## 🌐 Global Top 20")
        lines.append("")
        if global_top20:
            for i, entry in enumerate(global_top20[:20], 1):
                lines.extend(self._format_setup_entry(i, entry))
                lines.append(f"**Best Setup:** {entry.get('best_setup_type', 'n/a')} | **Global Score:** {float(entry.get('global_score', 0.0)):.2f} | **Confluence:** {int(entry.get('confluence', 1))}")
                lines.append("")
        else:
            lines.append("*No global setups found.*")
            lines.append("")

        lines.append("---")
        lines.append("")
        
        # Reversal Setups (Priority)
        lines.append("## 🔄 Top Reversal Setups")
        lines.append("")
        lines.append("*Downtrend → Base → Reclaim*")
        lines.append("")
        
        if reversal_results:
            top_reversals = reversal_results[:self.top_n]
            for i, entry in enumerate(top_reversals, 1):
                lines.extend(self._format_setup_entry(i, entry))
        else:
            lines.append("*No reversal setups found.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Breakout Setups
        lines.append("## 📈 Top Breakout Setups")
        lines.append("")
        lines.append("*Range break + volume confirmation*")
        lines.append("")
        
        if breakout_results:
            top_breakouts = breakout_results[:self.top_n]
            for i, entry in enumerate(top_breakouts, 1):
                lines.extend(self._format_setup_entry(i, entry))
        else:
            lines.append("*No breakout setups found.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Pullback Setups
        lines.append("## 📽 Top Pullback Setups")
        lines.append("")
        lines.append("*Trend continuation after retracement*")
        lines.append("")
        
        if pullback_results:
            top_pullbacks = pullback_results[:self.top_n]
            for i, entry in enumerate(top_pullbacks, 1):
                lines.extend(self._format_setup_entry(i, entry))
        else:
            lines.append("*No pullback setups found.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Footer
        lines.append("## Notes")
        lines.append("")
        lines.append("- Scores range from 0-100")
        lines.append("- Higher scores indicate stronger setups")
        lines.append("- ⚠️ flags indicate warnings (overextension, low liquidity, etc.)")
        lines.append("- This is a research tool, not financial advice")
        lines.append("")
        
        return "\n".join(lines)
    
    def _format_setup_entry(self, rank: int, data: dict) -> List[str]:
        """
        Format a single setup entry for markdown output.
        
        Args:
            rank: Position in ranking (1-based)
            data: Setup data dict containing symbol, score, components, etc.
        
        Returns:
            List of markdown lines
        """
        lines = []
        
        # Extract data
        symbol = data.get('symbol', 'UNKNOWN')
        coin_name = data.get('coin_name', 'Unknown')
        score = data.get('score', 0)
        raw_score = data.get('raw_score')
        penalty_multiplier = data.get('penalty_multiplier')
        price = data.get('price_usdt')
        
        # Header with rank, symbol, name, and score
        lines.append(f"### {rank}. {symbol} ({coin_name}) - Score: {score:.1f}")
        lines.append("")

        # Score transparency
        if raw_score is not None or penalty_multiplier is not None:
            raw_display = f"{float(raw_score):.2f}" if raw_score is not None else "n/a"
            pm_display = f"{float(penalty_multiplier):.4f}" if penalty_multiplier is not None else "n/a"
            lines.append(f"**Score Details:** score={float(score):.2f}, raw_score={raw_display}, penalty_multiplier={pm_display}")
            lines.append("")
        
        # Price
        if price is not None:
            lines.append(f"**Price:** ${price:.6f} USDT")
            lines.append("")
        
        # Components
        components = data.get('components', {})
        if components:
            lines.append("**Components:**")
            for comp_name, comp_value in components.items():
                lines.append(f"- {comp_name.replace('_', ' ').capitalize()}: {comp_value:.1f}")
            lines.append("")
        
        # Analysis
        analysis = data.get('analysis', '')
        if analysis:
            lines.append("**Analysis:**")
            if isinstance(analysis, str):
                lines.append(analysis)
            else:
                lines.append(json.dumps(analysis, ensure_ascii=False))
            lines.append("")
        
        # Flags - handle both dict and list formats
        flags = data.get('flags', {})
        flag_list = []
        
        if isinstance(flags, dict):
            flag_list = [k for k, v in flags.items() if v]
        elif isinstance(flags, list):
            flag_list = flags
        
        if flag_list:
            flag_str = ', '.join(flag_list)
            lines.append(f"**⚠️ Flags:** {flag_str}")
            lines.append("")
        
        return lines
        
    @staticmethod
    def _with_rank(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return entries with explicit 1-based rank preserving order."""
        ranked = []
        for idx, entry in enumerate(entries, start=1):
            ranked_entry = dict(entry)
            ranked_entry["rank"] = idx
            ranked.append(ranked_entry)
        return ranked

    def generate_json_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None,
        btc_regime: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate JSON report.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata dict
        
        Returns:
            Report dict (JSON-serializable)
        """
        report = {
            'schema_version': REPORT_SCHEMA_VERSION,
            'meta': {
                'date': run_date,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'version': REPORT_META_VERSION
            },
            'summary': {
                'reversal_count': len(reversal_results),
                'breakout_count': len(breakout_results),
                'pullback_count': len(pullback_results),
                'total_scored': len(reversal_results) + len(breakout_results) + len(pullback_results),
                'global_top20_count': len(global_top20)
            },
            'setups': {
                'reversals': self._with_rank(reversal_results[:self.top_n]),
                'breakouts': self._with_rank(breakout_results[:self.top_n]),
                'pullbacks': self._with_rank(pullback_results[:self.top_n]),
                'global_top20': self._with_rank(global_top20[:20])
            },
            'btc_regime': btc_regime or {
                'state': 'RISK_OFF',
                'multiplier_risk_on': 1.0,
                'multiplier_risk_off': 0.85,
                'checks': {
                    'close_gt_ema50': False,
                    'ema20_gt_ema50': False,
                },
            },
        }
        
        if metadata:
            report['meta'].update(metadata)
        
        return report
    
    def save_reports(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None,
        btc_regime: Dict[str, Any] = None,
    ) -> Dict[str, Path]:
        """
        Generate and save Markdown, JSON, and Excel reports.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata
        
        Returns:
            Dict with paths: {'markdown': Path, 'json': Path, 'excel': Path}
        """
        logger.info(f"Generating reports for {run_date}")
        
        # Generate Markdown
        md_content = self.generate_markdown_report(
            reversal_results, breakout_results, pullback_results, global_top20, run_date, btc_regime=btc_regime
        )
        
        # Generate JSON
        json_content = self.generate_json_report(
            reversal_results, breakout_results, pullback_results, global_top20, run_date, metadata, btc_regime=btc_regime
        )
        
        # Save Markdown
        md_path = self.reports_dir / f"{run_date}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Markdown report saved: {md_path}")
        
        # Save JSON
        json_path = self.reports_dir / f"{run_date}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON report saved: {json_path}")
        
        # Generate Excel
        try:
            from .excel_output import ExcelReportGenerator
            # Reconstruct config dict for Excel generator
            excel_config = {
                'output': {
                    'reports_dir': str(self.reports_dir),
                    'top_n_per_setup': self.top_n
                }
            }
            excel_gen = ExcelReportGenerator(excel_config)
            excel_path = excel_gen.generate_excel_report(
                reversal_results, breakout_results, pullback_results, global_top20, run_date, metadata, btc_regime=btc_regime
            )
            logger.info(f"Excel report saved: {excel_path}")
        except ImportError:
            logger.warning("openpyxl not installed - Excel export skipped")
            excel_path = None
        except Exception as e:
            logger.error(f"Excel generation failed: {e}")
            excel_path = None
        
        result = {
            'markdown': md_path,
            'json': json_path
        }
        
        if excel_path:
            result['excel'] = excel_path
        
        return result
