import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import pandas as pd
import logging
from typing import List, Optional

logger = logging.getLogger("ChartGenerator")

class ChartGenerator:
    """
    Generates static chart images for Telegram Bot.
    Aesthetic: Dark Mode / Terminal / Cyberpunk.
    """
    
    def __init__(self):
        # Configure plotting style - Clean White Mode
        plt.style.use('default') 
        
        # Professional "Bloomberg-style" Light Palette
        self.color_bg = '#ffffff'
        self.color_grid = '#f0f0f0'
        self.color_text = '#1a1a1a' # Almost Black
        self.color_up = '#00a800'   # Darker Green
        self.color_down = '#d10000' # Darker Red
        
        self.color_sma_fast = '#2962ff' # Blue (20)
        self.color_sma_slow = '#ff6d00' # Orange (50)
        
    def generate_chart(self, symbol: str, df: pd.DataFrame, title: str = None, markers: List[dict] = None, extra_lines: List[dict] = None, zones: List[dict] = None) -> Optional[BytesIO]:
        """
        Generates a chart image buffer from a DataFrame.
        DataFrame must have 'timestamp' (ms) and 'close'.
        """
        try:
            if df.empty:
                return None
                
            # Prepare Data
            df = df.copy()
            if 'timestamp' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            elif df.index.name == 'timestamp' or isinstance(df.index, pd.DatetimeIndex):
                df['date'] = df.index
            
            df = df.sort_values('date')
            
            # FORCE NUMERIC TYPES
            cols = ['open', 'high', 'low', 'close', 'volume']
            for c in cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            
            # --- INDICATORS ---
            # SMA 20 (Fast)
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            # SMA 50 (Slow)
            df['SMA_50'] = df['close'].rolling(window=50).mean()
            
            # Setup Figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, 
                                           gridspec_kw={'height_ratios': [3, 1]})
            fig.patch.set_facecolor(self.color_bg)
            
            # Subplot 1: Price
            ax1.set_facecolor(self.color_bg)
            ax1.grid(True, color=self.color_grid, linestyle='-', alpha=0.6)
            
            # Plot Price Line
            ax1.plot(df['date'], df['close'], color='#333333', linewidth=1.2, label='Price', zorder=3)
            ax1.fill_between(df['date'], df['close'], df['close'].min(), color='#e3f2fd', alpha=0.4, zorder=2)
            
            # Plot Indicators
            ax1.plot(df['date'], df['SMA_20'], color=self.color_sma_fast, linewidth=1.0, label='SMA 20', alpha=0.8, zorder=4)
            ax1.plot(df['date'], df['SMA_50'], color=self.color_sma_slow, linewidth=1.0, label='SMA 50', alpha=0.8, zorder=4)
            
            # Legend
            ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#e0e0e0', fontsize=8)
            
            # Annotate Last Price
            last_price = df.iloc[-1]['close']
            last_date = df.iloc[-1]['date']
            
            # Dynamic Arrow Color
            close_color = self.color_up if df.iloc[-1]['close'] >= df.iloc[0]['close'] else self.color_down
            
            ax1.annotate(f"${last_price:,.2f}", 
                         xy=(last_date, last_price),
                         xytext=(10, 0), textcoords='offset points',
                         color='white', fontsize=10, weight='bold',
                         bbox=dict(boxstyle="round,pad=0.3", fc=close_color, ec="none"))


            # --- EVENTS / MARKERS ---
            if markers:
                for m in markers:
                    # m = {'date': datetime, 'label': 'News', 'color': 'red'}
                    m_date = m.get('date')
                    m_label = m.get('label', '')
                    m_color = m.get('color', '#ff0000')
                    
                    if m_date:
                        ax1.axvline(x=m_date, color=m_color, linestyle='--', alpha=0.6, linewidth=0.8)
                        # Label at top
                        ylim = ax1.get_ylim()
                        y_text = ylim[1] - (ylim[1]-ylim[0])*0.05
                        ax1.text(m_date, y_text, m_label, rotation=90, verticalalignment='top', 
                                 fontsize=7, color=m_color, backgroundcolor=self.color_bg)

            # --- ZONES (Support/Resistance/Entry) ---
            if zones:
                for z in zones:
                    # z = {'y_min': float, 'y_max': float, 'color': hex, 'label': str, 'alpha': 0.2}
                    y_min = z.get('y_min')
                    y_max = z.get('y_max')
                    z_color = z.get('color', '#00a800')
                    z_alpha = z.get('alpha', 0.15)
                    z_label = z.get('label', '')
                    
                    if y_min and y_max:
                        ax1.axhspan(y_min, y_max, color=z_color, alpha=z_alpha, linewidth=0)
                        # Optional label
                        if z_label:
                            mid_y = (y_min + y_max) / 2
                            ax1.text(1.01, mid_y, z_label, transform=ax1.get_yaxis_transform(),
                                     fontsize=8, color=z_color, verticalalignment='center', weight='bold')

            # --- HORIZONTAL LINES (Levels) ---
            if extra_lines:
                 for l in extra_lines:
                    # l = {'y': float, 'color': hex, 'label': str, 'style': '--'}
                    y_val = l.get('y')
                    l_color = l.get('color', '#333333')
                    l_label = l.get('label', '')
                    l_style = l.get('style', '--')
                    
                    if y_val:
                        ax1.axhline(y=y_val, color=l_color, linestyle=l_style, alpha=0.9, linewidth=1.0)
                        # Label on right axis
                        xlim = ax1.get_xlim()
                        # Place label slightly inside the right edge
                        # Since x-axis is dates, utilize relative positioning transform
                        ax1.text(1.01, y_val, l_label, transform=ax1.get_yaxis_transform(),
                                 fontsize=8, color='white', verticalalignment='center',
                                 bbox=dict(boxstyle="round,pad=0.2", fc=l_color, ec="none", alpha=0.8))

            if title:
                ax1.set_title(title, color=self.color_text, fontsize=14, weight='bold', pad=20)
            else:
                ax1.set_title(f"{symbol} • 48H Trend", color=self.color_text, fontsize=14, weight='bold')

            # Subplot 2: Volume
            ax2.set_facecolor(self.color_bg)
            ax2.grid(True, color=self.color_grid, linestyle=':', alpha=0.6)
            
            if 'volume' in df.columns:
                # Color volume bars based on close vs prev close (approx)
                # Or just simple grey
                colors = ['#b0bec5'] * len(df)
                # If we have open, use open/close color
                if 'open' in df.columns:
                     colors = [self.color_up if c >= o else self.color_down for c, o in zip(df['close'], df['open'])]
                     # Make volume colors slightly transparent/pastel
                     colors = [c + '80' if len(c) == 7 else c for c in colors] # Adding alpha hex if needed, but matplotlib handles hex alpha differently.
                     # Actually standard matplotlib hex alpha is #RRGGBBAA
                
                ax2.bar(df['date'], df['volume'], color=colors, alpha=0.6, width=0.04)
            
            ax2.set_ylabel("Vol", color='#666666', fontsize=8)
            
            # Formatting Date Axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d/%m'))
            plt.xticks(rotation=0, color='#666666', fontsize=9)
            plt.yticks(color='#666666', fontsize=9)
            ax1.tick_params(axis='y', colors='#666666', labelsize=9)
            
            # Remove borders
            for ax in [ax1, ax2]:
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color('#cccccc')
                ax.spines['left'].set_color('#cccccc')

            plt.tight_layout()
            
            # Save to Buffer
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            
            return buf
            
        except Exception as e:
            logger.error(f"Chart Generation Error: {e}")
            return None

# Singleton
_chart_gen = None

def get_chart_generator():
    global _chart_gen
    if _chart_gen is None:
        _chart_gen = ChartGenerator()
    return _chart_gen
