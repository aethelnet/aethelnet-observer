"""
Week Test Harness - 7-Day Trading Validation System
Tracks daily performance and validates readiness for live trading
"""
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger("WeekTestHarness")

@dataclass
class DayMetrics:
    day: int  # 1-7
    date: str
    trades_count: int
    winning_trades: int
    total_pnl: float
    max_drawdown: float
    win_rate: float
    largest_loss: float
    largest_win: float
    avg_hold_time: float
    status: str  # "PASS", "FAIL", "PENDING"

@dataclass
class WeekTestResults:
    start_date: str
    current_day: int
    days: List[DayMetrics]
    overall_pnl: float
    overall_win_rate: float
    max_overall_drawdown: float
    is_complete: bool
    is_passing: bool
    live_ready: bool

class WeekTestHarness:
    """7-Day trading validation system"""
    
    PERSISTENCE_FILE = "week_test_results.json"
    
    # Validation Gates
    DAILY_WIN_RATE_THRESHOLD = 0.48  # 48%
    DAILY_MAX_DRAWDOWN = 0.05  # 5%
    DAILY_MIN_TRADES = 5
    MAX_SINGLE_LOSS = 0.02  # 2%
    
    WEEKLY_WIN_RATE_THRESHOLD = 0.50  # 50%
    WEEKLY_MAX_DRAWDOWN = 0.08  # 8%
    MIN_DAILY_WIN_RATE = 0.40  # 40% (no day below this)
    
    def __init__(self):
        self.current_test: Optional[WeekTestResults] = None
        self.daily_trades = []  # Reset daily
        self.daily_start_balance = 0.0
        self.daily_peak_balance = 0.0
        self.load_from_disk()
        
        logger.info("📅 Week Test Harness initialized")
    
    def start_week_test(self, initial_balance: float = 10000.0) -> bool:
        """Start a new 7-day test period"""
        if self.current_test and not self.current_test.is_complete:
            logger.warning("Week test already in progress")
            return False
        
        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        self.current_test = WeekTestResults(
            start_date=start_date,
            current_day=1,
            days=[],
            overall_pnl=0.0,
            overall_win_rate=0.0,
            max_overall_drawdown=0.0,
            is_complete=False,
            is_passing=False,
            live_ready=False
        )
        
        self.daily_start_balance = initial_balance
        self.daily_peak_balance = initial_balance
        self.daily_trades = []
        
        self.save_to_disk()
        logger.info(f"🚀 Week test started: Day 1/7 ({start_date})")
        return True
    
    def record_trade(self, trade_data: Dict[str, Any]):
        """Record a trade for daily metrics"""
        if not self.is_active():
            return
        
        self.daily_trades.append({
            'pnl': trade_data.get('pnl', 0.0),
            'hold_time': trade_data.get('hold_time', 0.0),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Check for immediate alerts
        pnl = trade_data.get('pnl', 0.0)
        if pnl < -self.daily_start_balance * self.MAX_SINGLE_LOSS:
            logger.warning(f"🚨 LARGE LOSS ALERT: ${pnl:.2f} exceeds {self.MAX_SINGLE_LOSS*100}% threshold")
    
    def end_trading_day(self, current_balance: float):
        """Process end-of-day metrics and validation"""
        if not self.is_active():
            return
        
        # Calculate daily metrics
        total_trades = len(self.daily_trades)
        winning_trades = sum(1 for t in self.daily_trades if t['pnl'] > 0)
        total_pnl = sum(t['pnl'] for t in self.daily_trades)
        
        win_rate = winning_trades / max(total_trades, 1)
        
        # Calculate drawdown
        daily_drawdown = max(0, (self.daily_peak_balance - current_balance) / self.daily_start_balance)
        
        # Find largest win/loss
        pnls = [t['pnl'] for t in self.daily_trades] if self.daily_trades else [0]
        largest_win = max(pnls) if pnls else 0
        largest_loss = min(pnls) if pnls else 0
        
        # Average hold time
        hold_times = [t['hold_time'] for t in self.daily_trades] if self.daily_trades else [0]
        avg_hold_time = sum(hold_times) / max(len(hold_times), 1)
        
        # Validate daily gates
        status = self._validate_daily_gates(
            total_trades, win_rate, daily_drawdown, largest_loss
        )
        
        # Create day metrics
        day_metrics = DayMetrics(
            day=self.current_test.current_day,
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            trades_count=total_trades,
            winning_trades=winning_trades,
            total_pnl=total_pnl,
            max_drawdown=daily_drawdown,
            win_rate=win_rate,
            largest_loss=largest_loss,
            largest_win=largest_win,
            avg_hold_time=avg_hold_time,
            status=status
        )
        
        self.current_test.days.append(day_metrics)
        
        # Update overall metrics
        self._update_overall_metrics()
        
        # Log daily summary
        logger.info(f"📊 Day {self.current_test.current_day}/7 Complete:")
        logger.info(f"   Trades: {total_trades} | Win Rate: {win_rate:.1%} | P&L: ${total_pnl:.2f}")
        logger.info(f"   Drawdown: {daily_drawdown:.1%} | Status: {status}")
        
        # Check if week is complete
        if self.current_test.current_day >= 7:
            self._complete_week_test()
        else:
            # Advance to next day
            self.current_test.current_day += 1
            self._reset_daily_counters(current_balance)
        
        self.save_to_disk()
    
    def _validate_daily_gates(self, trades: int, win_rate: float, drawdown: float, largest_loss: float) -> str:
        """Validate daily performance gates"""
        failures = []
        
        if trades < self.DAILY_MIN_TRADES:
            failures.append(f"Insufficient trades ({trades} < {self.DAILY_MIN_TRADES})")
        
        if win_rate < self.DAILY_WIN_RATE_THRESHOLD:
            failures.append(f"Low win rate ({win_rate:.1%} < {self.DAILY_WIN_RATE_THRESHOLD:.1%})")
        
        if drawdown > self.DAILY_MAX_DRAWDOWN:
            failures.append(f"High drawdown ({drawdown:.1%} > {self.DAILY_MAX_DRAWDOWN:.1%})")
        
        if largest_loss < -self.daily_start_balance * self.MAX_SINGLE_LOSS:
            failures.append(f"Large single loss (${largest_loss:.2f})")
        
        if failures:
            logger.warning(f"❌ Daily gates FAILED: {', '.join(failures)}")
            return "FAIL"
        else:
            logger.info("[OK] Daily gates PASSED")
            return "PASS"
    
    def _update_overall_metrics(self):
        """Update overall week metrics"""
        if not self.current_test.days:
            return
        
        # Overall P&L
        self.current_test.overall_pnl = sum(day.total_pnl for day in self.current_test.days)
        
        # Overall win rate
        total_trades = sum(day.trades_count for day in self.current_test.days)
        total_wins = sum(day.winning_trades for day in self.current_test.days)
        self.current_test.overall_win_rate = total_wins / max(total_trades, 1)
        
        # Max overall drawdown
        self.current_test.max_overall_drawdown = max(day.max_drawdown for day in self.current_test.days)
    
    def _complete_week_test(self):
        """Complete the week test and validate overall performance"""
        self.current_test.is_complete = True
        
        # Validate weekly gates
        failures = []
        
        if self.current_test.overall_win_rate < self.WEEKLY_WIN_RATE_THRESHOLD:
            failures.append(f"Low overall win rate ({self.current_test.overall_win_rate:.1%})")
        
        if self.current_test.overall_pnl <= 0:
            failures.append(f"Negative overall P&L (${self.current_test.overall_pnl:.2f})")
        
        if self.current_test.max_overall_drawdown > self.WEEKLY_MAX_DRAWDOWN:
            failures.append(f"High overall drawdown ({self.current_test.max_overall_drawdown:.1%})")
        
        # Check for any day below minimum win rate
        min_daily_win_rate = min(day.win_rate for day in self.current_test.days)
        if min_daily_win_rate < self.MIN_DAILY_WIN_RATE:
            failures.append(f"Day with very low win rate ({min_daily_win_rate:.1%})")
        
        # Check for any failed days
        failed_days = [day.day for day in self.current_test.days if day.status == "FAIL"]
        if failed_days:
            failures.append(f"Failed days: {failed_days}")
        
        if failures:
            self.current_test.is_passing = False
            self.current_test.live_ready = False
            logger.warning(f"❌ WEEK TEST FAILED: {', '.join(failures)}")
        else:
            self.current_test.is_passing = True
            self.current_test.live_ready = True
            logger.info("🎉 WEEK TEST PASSED - LIVE TRADING READY!")
        
        # Generate final report
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate comprehensive week test report"""
        report = f"""
=== WEEK TEST FINAL REPORT ===
Start Date: {self.current_test.start_date}
Duration: 7 days
Status: {'PASSED' if self.current_test.is_passing else 'FAILED'}
Live Ready: {'YES' if self.current_test.live_ready else 'NO'}

OVERALL METRICS:
- Total P&L: ${self.current_test.overall_pnl:.2f}
- Win Rate: {self.current_test.overall_win_rate:.1%}
- Max Drawdown: {self.current_test.max_overall_drawdown:.1%}

DAILY BREAKDOWN:
"""
        for day in self.current_test.days:
            report += f"Day {day.day}: {day.status} | Trades: {day.trades_count} | Win Rate: {day.win_rate:.1%} | P&L: ${day.total_pnl:.2f}\n"
        
        report += f"\nGenerated: {datetime.now(timezone.utc).isoformat()}\n"
        
        # Save report to file
        with open("week_test_final_report.txt", "w") as f:
            f.write(report)
        
        logger.info("📋 Final report saved to week_test_final_report.txt")
    
    def _reset_daily_counters(self, new_start_balance: float):
        """Reset counters for new trading day"""
        self.daily_trades = []
        self.daily_start_balance = new_start_balance
        self.daily_peak_balance = new_start_balance
    
    def is_active(self) -> bool:
        """Check if week test is currently active"""
        return (self.current_test is not None and 
                not self.current_test.is_complete)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current test status for dashboard"""
        if not self.current_test:
            return {
                "active": False,
                "message": "No week test in progress"
            }
        
        # Calculate progress
        progress = (self.current_test.current_day - 1) / 7 * 100
        days_remaining = 8 - self.current_test.current_day
        
        # Current day metrics
        current_day_trades = len(self.daily_trades)
        current_day_wins = sum(1 for t in self.daily_trades if t['pnl'] > 0)
        current_day_win_rate = current_day_wins / max(current_day_trades, 1)
        current_day_pnl = sum(t['pnl'] for t in self.daily_trades)
        
        return {
            "active": True,
            "current_day": self.current_test.current_day,
            "progress_percent": progress,
            "days_remaining": days_remaining,
            "is_complete": self.current_test.is_complete,
            "is_passing": self.current_test.is_passing,
            "live_ready": self.current_test.live_ready,
            "overall_pnl": self.current_test.overall_pnl,
            "overall_win_rate": self.current_test.overall_win_rate,
            "current_day_trades": current_day_trades,
            "current_day_win_rate": current_day_win_rate,
            "current_day_pnl": current_day_pnl,
            "completed_days": [asdict(day) for day in self.current_test.days],
            "start_date": self.current_test.start_date
        }
    
    def save_to_disk(self):
        """Save test results to disk"""
        if not self.current_test:
            return
        
        try:
            with open(self.PERSISTENCE_FILE, 'w') as f:
                json.dump(asdict(self.current_test), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save week test results: {e}")
    
    def load_from_disk(self):
        """Load test results from disk"""
        if not os.path.exists(self.PERSISTENCE_FILE):
            return
        
        try:
            with open(self.PERSISTENCE_FILE, 'r') as f:
                data = json.load(f)
            
            # Reconstruct objects
            days = [DayMetrics(**day) for day in data.get('days', [])]
            data['days'] = days
            
            self.current_test = WeekTestResults(**data)
            logger.info(f"📂 Loaded week test: Day {self.current_test.current_day}/7")
            
        except Exception as e:
            logger.error(f"Failed to load week test results: {e}")

# Global instance
_week_test_harness: Optional[WeekTestHarness] = None

def get_week_test_harness() -> WeekTestHarness:
    """Get or create week test harness instance"""
    global _week_test_harness
    if _week_test_harness is None:
        _week_test_harness = WeekTestHarness()
    return _week_test_harness
