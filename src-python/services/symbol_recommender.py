"""
Symbol Recommendation Service (Phase 2)

Generates periodic reports with symbol recommendations for manual review.
Reports suggest symbols to remove (underperformers) and add (high liquidity).
All recommendations require manual approval - no automatic changes.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
import time
from typing import Dict, Any, Optional
from pathlib import Path

from config import get_settings
from scripts.analyze_win_rate import (
    collect_trades,
    by_symbol_stats,
    generate_symbol_recommendations
)

logger = logging.getLogger("SymbolRecommender")

class SymbolRecommender:
    """
    Generates periodic symbol recommendations based on profitability analysis.
    Reports are saved to disk and can be viewed via API or manually.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.report_path = Path(self.settings.SYMBOL_REPORT_PATH)
        self.last_report_time: Optional[float] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a new symbol recommendation report.
        Returns report dictionary with recommendations and metadata.
        """
        logger.info("[SYMBOL_RECOMMENDER] Generating symbol recommendation report...")
        
        try:
            # Collect trade data
            trades = collect_trades()
            if not trades:
                logger.warning("[SYMBOL_RECOMMENDER] No trade data available for recommendations")
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "no_data",
                    "message": "No trade data available",
                    "remove": [],
                    "add": [],
                    "keep": []
                }
            
            # Calculate per-symbol stats
            stats = by_symbol_stats(trades)
            
            # Generate recommendations
            recommendations = generate_symbol_recommendations(stats, self.settings)
            
            # Build comprehensive report
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                "total_symbols_analyzed": len(stats),
                "total_trades": len(trades),
                "recommendations": recommendations,
                "summary": {
                    "symbols_to_remove": len(recommendations.get("remove", [])),
                    "symbols_to_add": len(recommendations.get("add", [])),
                    "top_performers": len(recommendations.get("keep", []))
                },
                "current_trading_symbols": list(self._get_current_symbols()),
                "settings": {
                    "min_trades_threshold": self.settings.SYMBOL_REPORT_MIN_TRADES,
                    "report_interval_hours": self.settings.SYMBOL_REPORT_INTERVAL_HOURS
                }
            }
            
            # Save report to disk
            self._save_report(report)
            self.last_report_time = time.time()
            
            logger.info(
                f"[SYMBOL_RECOMMENDER] Report generated: "
                f"Remove={report['summary']['symbols_to_remove']}, "
                f"Add={report['summary']['symbols_to_add']}, "
                f"Keep={report['summary']['top_performers']}"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"[SYMBOL_RECOMMENDER] Error generating report: {e}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e),
                "remove": [],
                "add": [],
                "keep": []
            }
    
    def _get_current_symbols(self) -> set:
        """Get current trading symbols from settings."""
        try:
            from config.settings import get_trading_symbols
            return set(get_trading_symbols(self.settings))
        except Exception:
            return set()
    
    def _save_report(self, report: Dict[str, Any]) -> None:
        """Save report to disk as JSON."""
        try:
            # Ensure directory exists
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write report
            with open(self.report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.debug(f"[SYMBOL_RECOMMENDER] Report saved to {self.report_path}")
        except Exception as e:
            logger.error(f"[SYMBOL_RECOMMENDER] Failed to save report: {e}")
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Load the latest saved report from disk."""
        try:
            if not self.report_path.exists():
                return None
            
            with open(self.report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[SYMBOL_RECOMMENDER] Failed to load report: {e}")
            return None
    
    async def _periodic_report_loop(self) -> None:
        """Background task that generates reports periodically."""
        interval_seconds = self.settings.SYMBOL_REPORT_INTERVAL_HOURS * 3600
        
        logger.info(
            f"[SYMBOL_RECOMMENDER] Starting periodic report generation "
            f"(interval: {self.settings.SYMBOL_REPORT_INTERVAL_HOURS} hours)"
        )
        
        while self.is_running:
            try:
                # Generate report
                await self.generate_report()
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                logger.info("[SYMBOL_RECOMMENDER] Periodic report loop cancelled")
                break
            except Exception as e:
                logger.error(f"[SYMBOL_RECOMMENDER] Error in periodic loop: {e}", exc_info=True)
                # Wait a bit before retrying on error
                await asyncio.sleep(3600)  # 1 hour
    
    def start(self) -> None:
        """Start the periodic report generation task."""
        if not self.settings.AUTO_SYMBOL_SUGGESTIONS:
            logger.info("[SYMBOL_RECOMMENDER] Auto suggestions disabled in settings")
            return
        
        if self.is_running:
            logger.warning("[SYMBOL_RECOMMENDER] Already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._periodic_report_loop(), name="symbol_recommender")
        logger.info("[SYMBOL_RECOMMENDER] Started periodic report generation")
    
    def stop(self) -> None:
        """Stop the periodic report generation task."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("[SYMBOL_RECOMMENDER] Stopped periodic report generation")
    
    def format_report_for_display(self, report: Optional[Dict[str, Any]] = None) -> str:
        """
        Format report as human-readable text for console/logs.
        """
        if report is None:
            report = self.get_latest_report()
        
        if not report:
            return "No report available"
        
        if report.get("status") != "success":
            return f"Report status: {report.get('status')} - {report.get('message', report.get('error', 'Unknown error'))}"
        
        lines = []
        lines.append("=" * 60)
        lines.append("SYMBOL RECOMMENDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {report.get('timestamp', 'Unknown')}")
        lines.append(f"Total Symbols Analyzed: {report.get('total_symbols_analyzed', 0)}")
        lines.append(f"Total Trades: {report.get('total_trades', 0)}")
        lines.append("")
        
        recs = report.get("recommendations", {})
        
        # Symbols to Remove
        remove_list = recs.get("remove", [])
        if remove_list:
            lines.append("[WARN]  SYMBOLS TO CONSIDER REMOVING:")
            lines.append("-" * 60)
            for item in remove_list[:10]:  # Top 10 worst
                lines.append(
                    f"  • {item['symbol']}: {item['reason']} "
                    f"(trades={item['total_trades']}, PnL=${item['cumulative_pnl']:.2f}, "
                    f"win_rate={item['win_rate']*100:.1f}%)"
                )
            lines.append("")
        
        # Symbols to Add
        add_list = recs.get("add", [])
        if add_list:
            lines.append("[OK] SYMBOLS TO CONSIDER ADDING:")
            lines.append("-" * 60)
            for item in add_list[:10]:  # Top 10 suggestions
                lines.append(f"  • {item['symbol']}: {item['reason']}")
            lines.append("")
        
        # Top Performers
        keep_list = recs.get("keep", [])
        if keep_list:
            lines.append("⭐ TOP PERFORMERS (Keep These):")
            lines.append("-" * 60)
            for item in keep_list[:10]:  # Top 10 best
                lines.append(
                    f"  • {item['symbol']}: {item['reason']} "
                    f"(trades={item['total_trades']}, PnL=${item['cumulative_pnl']:.2f}, "
                    f"win_rate={item['win_rate']*100:.1f}%)"
                )
            lines.append("")
        
        if not remove_list and not add_list and not keep_list:
            lines.append("No recommendations at this time.")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("Review this report and manually update BASE_CURRENCIES/QUOTE_CURRENCIES")
        lines.append("in your .env file if you want to implement these recommendations.")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Singleton instance
_recommender_instance: Optional[SymbolRecommender] = None

def get_symbol_recommender() -> SymbolRecommender:
    """Get or create the singleton SymbolRecommender instance."""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = SymbolRecommender()
    return _recommender_instance


