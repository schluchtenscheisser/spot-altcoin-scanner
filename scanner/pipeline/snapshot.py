"""
Snapshot System
===============

Creates deterministic daily snapshots for backtesting and reproducibility.
Snapshots include all pipeline data at a specific point in time.
"""

import logging
from typing import Dict, Any, List
import re
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Manages daily pipeline snapshots."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize snapshot manager.
        
        Args:
            config: Config dict with 'snapshots' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            snapshot_config = config.raw.get('snapshots', {})
        else:
            snapshot_config = config.get('snapshots', {})
        
        history_dir = snapshot_config.get('history_dir')
        snapshot_dir = snapshot_config.get('snapshot_dir')
        legacy_runtime_dir = snapshot_config.get('runtime_dir')

        resolved_dir = history_dir or snapshot_dir
        if resolved_dir is None and legacy_runtime_dir is not None:
            logger.warning(
                "snapshots.runtime_dir is deprecated for snapshot history; "
                "please migrate to snapshots.history_dir"
            )
            resolved_dir = legacy_runtime_dir

        self.snapshots_dir = Path(resolved_dir or 'snapshots/history')

        # Ensure directory exists
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Snapshot Manager initialized: {self.snapshots_dir}")
    
    def create_snapshot(
        self,
        run_date: str,
        universe: List[Dict[str, Any]],
        filtered: List[Dict[str, Any]],
        shortlist: List[Dict[str, Any]],
        features: Dict[str, Dict[str, Any]],
        reversal_scores: List[Dict[str, Any]],
        breakout_scores: List[Dict[str, Any]],
        pullback_scores: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> Path:
        """
        Create a complete snapshot of the pipeline run.
        
        Args:
            run_date: Date string (YYYY-MM-DD)
            universe: Full MEXC universe
            filtered: Post-filter universe
            shortlist: Shortlisted symbols
            features: Computed features
            reversal_scores: Reversal scoring results
            breakout_scores: Breakout scoring results
            pullback_scores: Pullback scoring results
            metadata: Optional metadata
        
        Returns:
            Path to saved snapshot file
        """
        logger.info(f"Creating snapshot for {run_date}")
        
        snapshot = {
            'meta': {
                'date': run_date,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0'
            },
            'pipeline': {
                'universe_count': len(universe),
                'filtered_count': len(filtered),
                'shortlist_count': len(shortlist),
                'features_count': len(features)
            },
            'data': {
                'universe': universe,
                'filtered': filtered,
                'shortlist': shortlist,
                'features': features
            },
            'scoring': {
                'reversals': reversal_scores,
                'breakouts': breakout_scores,
                'pullbacks': pullback_scores
            }
        }
        
        if metadata:
            snapshot['meta'].update(metadata)
            
        # Safety: ensure as-of exists (for reproducibility)
        if 'asof_ts_ms' not in snapshot['meta']:
            snapshot['meta']['asof_ts_ms'] = int(datetime.utcnow().timestamp() * 1000)

        if 'asof_iso' not in snapshot['meta']:
            snapshot['meta']['asof_iso'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
        # Save snapshot
        snapshot_path = self.snapshots_dir / f"{run_date}.json"
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        # Get file size
        size_mb = snapshot_path.stat().st_size / (1024 * 1024)
        
        logger.info(f"Snapshot saved: {snapshot_path} ({size_mb:.2f} MB)")
        
        return snapshot_path
    
    def load_snapshot(self, run_date: str) -> Dict[str, Any]:
        """
        Load a snapshot by date.
        
        Args:
            run_date: Date string (YYYY-MM-DD)
        
        Returns:
            Snapshot dict
        
        Raises:
            FileNotFoundError: If snapshot doesn't exist
        """
        snapshot_path = self.snapshots_dir / f"{run_date}.json"
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        
        logger.info(f"Loading snapshot: {snapshot_path}")
        
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        return snapshot
    
    def list_snapshots(self) -> List[str]:
        """
        List all available snapshot dates.
        
        Returns:
            List of date strings (YYYY-MM-DD)
        """
        snapshots = []

        for path in self.snapshots_dir.glob("*.json"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
                continue

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(payload, dict):
                continue
            if not all(key in payload for key in ('meta', 'pipeline', 'data', 'scoring')):
                continue

            snapshots.append(path.stem)

        snapshots.sort()

        logger.info(f"Found {len(snapshots)} snapshots")

        return snapshots
    
    def get_snapshot_stats(self, run_date: str) -> Dict[str, Any]:
        """
        Get statistics about a snapshot without loading full data.
        
        Args:
            run_date: Date string
        
        Returns:
            Stats dict
        """
        snapshot = self.load_snapshot(run_date)
        
        return {
            'date': snapshot['meta']['date'],
            'created_at': snapshot['meta']['created_at'],
            'universe_count': snapshot['pipeline']['universe_count'],
            'filtered_count': snapshot['pipeline']['filtered_count'],
            'shortlist_count': snapshot['pipeline']['shortlist_count'],
            'features_count': snapshot['pipeline']['features_count'],
            'reversal_count': len(snapshot['scoring']['reversals']),
            'breakout_count': len(snapshot['scoring']['breakouts']),
            'pullback_count': len(snapshot['scoring']['pullbacks'])
        }
