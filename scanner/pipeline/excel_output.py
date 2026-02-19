"""
Excel Output Generation
=======================

Generates Excel workbooks with multiple sheets for daily scanner results.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelReportGenerator:
    """Generates Excel reports with multiple sheets."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Excel report generator.
        
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
        
        logger.info(f"Excel Report Generator initialized: reports_dir={self.reports_dir}")
    
    def generate_excel_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None
    ) -> Path:
        """
        Generate Excel workbook with 4 sheets.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata (universe size, etc.)
        
        Returns:
            Path to saved Excel file
        """
        logger.info(f"Generating Excel report for {run_date}")
        
        # Create workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Sheet 1: Summary
        self._create_summary_sheet(
            wb, run_date, 
            len(reversal_results), 
            len(breakout_results), 
            len(pullback_results),
            metadata
        )
        
        # Sheet 2: Global Top 20
        self._create_global_sheet(wb, global_top20[:20])

        # Sheet 3: Reversal Setups
        self._create_setup_sheet(
            wb, "Reversal Setups", 
            reversal_results[:self.top_n],
            ['Drawdown', 'Base', 'Reclaim', 'Volume']
        )
        
        # Sheet 4: Breakout Setups
        self._create_setup_sheet(
            wb, "Breakout Setups",
            breakout_results[:self.top_n],
            ['Breakout', 'Volume', 'Trend', 'Momentum']
        )
        
        # Sheet 5: Pullback Setups
        self._create_setup_sheet(
            wb, "Pullback Setups",
            pullback_results[:self.top_n],
            ['Trend', 'Pullback', 'Rebound', 'Volume']
        )
        
        # Save
        excel_path = self.reports_dir / f"{run_date}.xlsx"
        wb.save(excel_path)
        logger.info(f"Excel report saved: {excel_path}")
        
        return excel_path
    
    def _create_summary_sheet(
        self,
        wb: Workbook,
        run_date: str,
        reversal_count: int,
        breakout_count: int,
        pullback_count: int,
        metadata: Dict[str, Any] = None
    ):
        """Create Summary sheet with run statistics."""
        ws = wb.create_sheet("Summary", 0)
        
        # Header
        ws['A1'] = 'Metric'
        ws['B1'] = 'Value'
        
        # Style header
        for cell in ['A1', 'B1']:
            ws[cell].font = Font(bold=True, size=12)
            ws[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            ws[cell].font = Font(bold=True, size=12, color="FFFFFF")
            ws[cell].alignment = Alignment(horizontal='center')
        
        # Data rows
        row = 2
        ws[f'A{row}'] = 'Run Date'
        ws[f'B{row}'] = run_date
        row += 1
        
        ws[f'A{row}'] = 'Generated At'
        ws[f'B{row}'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        row += 1
        
        # Add metadata if available
        if metadata:
            ws[f'A{row}'] = 'Total Symbols Scanned'
            ws[f'B{row}'] = metadata.get('universe_size', 'N/A')
            row += 1
            
            ws[f'A{row}'] = 'Symbols Filtered (MidCaps)'
            ws[f'B{row}'] = metadata.get('filtered_size', 'N/A')
            row += 1
            
            ws[f'A{row}'] = 'Symbols in Shortlist'
            ws[f'B{row}'] = metadata.get('shortlist_size', 'N/A')
            row += 1
        
        ws[f'A{row}'] = 'Reversal Setups Found'
        ws[f'B{row}'] = reversal_count
        row += 1
        
        ws[f'A{row}'] = 'Breakout Setups Found'
        ws[f'B{row}'] = breakout_count
        row += 1
        
        ws[f'A{row}'] = 'Pullback Setups Found'
        ws[f'B{row}'] = pullback_count
        row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
    

    def _create_global_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create Global Top 20 sheet."""
        ws = wb.create_sheet("Global Top 20", 1)
        headers = [
            'Rank', 'Symbol', 'Name', 'Best Setup', 'Global Score', 'Setup Score', 'Confluence',
            'Price (USDT)', 'Market Cap', '24h Volume', 'Flags'
        ]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True, size=11, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')

        for rank, result in enumerate(results, 1):
            row = rank + 1
            ws.cell(row=row, column=1, value=rank)
            ws.cell(row=row, column=2, value=result.get('symbol', 'N/A'))
            ws.cell(row=row, column=3, value=result.get('coin_name', 'Unknown'))
            ws.cell(row=row, column=4, value=result.get('best_setup_type', 'N/A'))
            ws.cell(row=row, column=5, value=float(result.get('global_score', 0.0)))
            ws.cell(row=row, column=6, value=float(result.get('setup_score', result.get('score', 0.0))))
            ws.cell(row=row, column=7, value=int(result.get('confluence', 1)))
            price = result.get('price_usdt')
            ws.cell(row=row, column=8, value=f"${price:.2f}" if price is not None else 'N/A')
            market_cap = result.get('market_cap')
            ws.cell(row=row, column=9, value=self._format_large_number(market_cap) if market_cap else 'N/A')
            volume = result.get('quote_volume_24h')
            ws.cell(row=row, column=10, value=self._format_large_number(volume) if volume else 'N/A')
            flags = result.get('flags', [])
            flag_str = ', '.join(flags) if isinstance(flags, list) else ''
            ws.cell(row=row, column=11, value=flag_str)

        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions

    def _create_setup_sheet(
        self,
        wb: Workbook,
        sheet_name: str,
        results: List[Dict[str, Any]],
        component_names: List[str]
    ):
        """
        Create a setup sheet (Reversal/Breakout/Pullback).
        
        Args:
            wb: Workbook object
            sheet_name: Name of the sheet
            results: List of scored setups
            component_names: List of component score names
        """
        ws = wb.create_sheet(sheet_name)
        
        # Headers
        headers = [
            'Rank', 'Symbol', 'Name', 'Price (USDT)', 
            'Market Cap', '24h Volume', 'Score'
        ] + component_names + ['Flags']
        
        # Write headers
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True, size=11)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(bold=True, size=11, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows
        for rank, result in enumerate(results, 1):
            row_idx = rank + 1
            
            # Basic info
            ws.cell(row=row_idx, column=1, value=rank)
            ws.cell(row=row_idx, column=2, value=result.get('symbol', 'N/A'))
            ws.cell(row=row_idx, column=3, value=result.get('coin_name', 'Unknown'))
            
            # Price
            price = result.get('price_usdt')
            if price is not None:
                ws.cell(row=row_idx, column=4, value=f"${price:.2f}")
            else:
                ws.cell(row=row_idx, column=4, value='N/A')
            
            # Market Cap (abbreviated)
            market_cap = result.get('market_cap')
            if market_cap:
                ws.cell(row=row_idx, column=5, value=self._format_large_number(market_cap))
            else:
                ws.cell(row=row_idx, column=5, value='N/A')
            
            # 24h Volume (abbreviated)
            volume = result.get('quote_volume_24h')
            if volume:
                ws.cell(row=row_idx, column=6, value=self._format_large_number(volume))
            else:
                ws.cell(row=row_idx, column=6, value='N/A')
            
            # Score
            ws.cell(row=row_idx, column=7, value=result.get('score', 0))
            
            # Component scores
            components = result.get('components', {})
            for col_offset, comp_name in enumerate(component_names):
                comp_key = comp_name.lower()
                comp_value = components.get(comp_key, 0)
                ws.cell(row=row_idx, column=8 + col_offset, value=comp_value)
            
            # Flags
            flags = result.get('flags', [])
            if isinstance(flags, list):
                flag_str = ', '.join(flags) if flags else ''
            elif isinstance(flags, dict):
                flag_str = ', '.join([k for k, v in flags.items() if v])
            else:
                flag_str = ''
            ws.cell(row=row_idx, column=8 + len(component_names), value=flag_str)
        
        # Freeze top row
        ws.freeze_panes = 'A2'
        
        # Autofilter
        ws.auto_filter.ref = ws.dimensions
        
        # Column widths
        ws.column_dimensions['A'].width = 6   # Rank
        ws.column_dimensions['B'].width = 14  # Symbol
        ws.column_dimensions['C'].width = 20  # Name
        ws.column_dimensions['D'].width = 13  # Price
        ws.column_dimensions['E'].width = 13  # Market Cap
        ws.column_dimensions['F'].width = 13  # Volume
        ws.column_dimensions['G'].width = 8   # Score
        
        # Component columns
        for i in range(len(component_names)):
            col_letter = get_column_letter(8 + i)
            ws.column_dimensions[col_letter].width = 12
        
        # Flags column
        flags_col = get_column_letter(8 + len(component_names))
        ws.column_dimensions[flags_col].width = 25
    
    def _format_large_number(self, num: float) -> str:
        """
        Format large numbers with M/B suffix.
        
        Args:
            num: Number to format
        
        Returns:
            Formatted string (e.g., "$1.23M", "$4.56B")
        """
        if num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num / 1_000:.2f}K"
        else:
            return f"${num:.2f}"
