"""
Pidgin Poet: The Soul of the Machine.
Generates market commentary in various African dialects (Nigerian Pidgin, Ghanaian Pie, SA Slang)
to provide amusement when the market is boring or chaotic.
"""

import random
from typing import Tuple

class PidginPoet:
    
    # High Impact Exclamations
    EXCLAMATIONS = [
        "BOMBACLAT!",
        "OLORUN MAJE!",
        "CHALE!",
        "YWEEH!",
        "MAD O!",
        "ODIEGWU!",
        "EISH!",
        "WEWE!",
        "A JE KUN IYA!",
        "CHAI!",
        "HAYIBO!",
        "OTILO!",
        "ZAGADAT!"
    ]

    # Narrative Lexicon
    # Keys map to Regimes
    LEXICON = {
        'BOREDOM': [
            "I look the chart, the chart look me. Nothing. Absolutely nothing. Even the candles are tired of moving. Maybe the market maker went to buy bread and forgot to come back.",
            "You think say market go just dash you money? Lai lai. The opportunity never ripe. It dey cook. If you rush am, you go eat raw yam. Patient dog chop fat bone, but starving dog die first.",
            "Wetin man go do? We go wait. The volume small pass church mouse wallet. Even the algorithm is asking if we should close shop and go watch football.",
            "Chale, send valid location. Oh wait, market no dey move. We are stuck in traffic on the blockchain. Just hold your hunger.",
            "Sideways movement. Crabs are winning today. The whales are sleeping, or maybe they are planning wickedness. Stay guarded.",
            "Abeg, go touch grass small. Come back later. Watching this candle paint one pixel every hour will give you hypertension.",
            "The universe is cold today. The heart of the machine is barely beating. 0.01% change in 3 hours? This is not trading, this is meditation.",
            "Ghost town on the order book. No activity. No signal. Just the wind blowing through the trenches.",
            "Even the bots are bored. I saw one trying to buy its own sell order just to feel something. Madness.",
            "Low volatility is a trap for the impatient. If you enter now, you are just providing liquidity for someone's dinner. Sit down.",
        ],
        
        'VOLATILITY': [
            "Wahala dey happen! Price dey run kitikiti! If you no get chest, close your eyes. This one no be play play.",
            "Omo! See violence! One green candle can change your life, one red candle can send you back to the village. Choose wisely.",
            "E don cast! Market is choosing violence today. Stop Loss is not enough, you need prayer warrior.",
            "Eish! The charts are shaking. One minute you differ, next minute you suffer. Fast fingers only.",
            "Zig zag everywhere. Stops getting hunted like bushmeat. The volatility is tasting like pepper soup—spicy but dangerous.",
            "Yebo! Only entering if you have heart of stone. The liquidity is splashing everywhere.",
            "The market is vibrating. Liquidations are dropping like rain. If you stay too long, you go soak.",
            "Total mayhem. High-frequency chaos. The machine is screaming. This is where the professionals separate from the dreamers.",
            "Price is jumping like a fish out of water. Catch it at the wrong time and it will slap you across the face. Be careful.",
            "Sigma levels detected. This is the extreme. The physics of the market are bending. Hold your breath.",
        ],
        
        'PUMP': [
            "To the moon ko? Oya na! Someone is printing money. I hope it is you, because if not, Sapa is looking for you.",
            "Green candles sweet pass Jollof rice. But remember, what goes up must come down... eventually. Take profit or take tears.",
            "Up only! Gravity is offline. The bulls have taken steroids. Bears are crying inside house.",
            "Look at that wicked wick! Straight up! FOMO is kicking, but don't buy the top o. I warn you.",
            "The rocket is leaving the station. No tickets left for the slow ones. If you are onboard, don't forget to pack your bags.",
            "Parabolic expansion. The chart is trying to leave the screen. This is the glory, but the crash is usually more silent.",
            "Massive buy walls. The whales are hungry today. They are eating everything in sight. Join the feast but watch the exit.",
        ],
        
        'DUMP': [
            "Sapa choke. Red sea everywhere. The brothers are holding bags heavier than cement.",
            "Gravity check! Everything going down. Floors are breaking. Cellars are opening. Don't catch the falling knife o.",
            "Omo. Bears took the wheel. They are driving us to the trenches. Hold firm or fold.",
            "Blood in the streets. Some call it disaster, some call it discount. Which one you be?",
            "The waterfall has started. No umbrellas on this level. Everyone is getting wet. Protect your capital or lose your sanity.",
            "Support is now resistance. The narrative has changed. The bag holders are praying, but the machine doesn't hear prayers.",
            "Capitulation. The weak hands are being shaken off. This is the purge. Only the cold-hearted survive the red sea.",
        ],
        
        'CONFUSION': [
            "Wetin be this? Up? Down? Nobody knows. The market is dancing shaku shaku with our emotions.",
            "Signals are mixed like salad. One indicator say buy, one say sell. Me, I say rest.",
            "Fakeout everywhere. The script writer is confused. Maybe AI took over and crashed.",
            "One leg in, one leg out. Whales playing ping pong with price. Don't be the ball.",
            "Indecision. The candle is spinning like a drunk man looking for his keys.",
            "The chart is a Rorschach test today. I see a butterfly, you see a liquidation. We are both wrong.",
            "Market is sideways-down-up-nowhere. The direction is 'Error 404'. Go and sleep.",
            "Chop city. If you trade here, you are just feeding the exchange's fees. Don't be a hero.",
        ],
        'DESPERATION': [
            "Omo, I promised my landlord money tomorrow. Market, do something!",
            "If this support breaks, I am going back to sell Gala in traffic.",
            "God of green candles, pick up my call. It's urgent.",
            "I checked my PnL and tears dropped. Who send me message?",
            "Just one pump. That's all I ask. Just one small accidental pump.",
            "Refreshing the chart every 2 seconds won't make it move, but I will do it anyway.",
            "My margin is callin' like a long lost friend. I don't want to pick up.",
        ],
        'PHILOSOPHY': [
            "What is money? Just numbers on a screen. Why are we stressing? (Because we are broke).",
            "The market is a reflection of human greed and fear. Right now, it smells like fear.",
            "To trade is to suffer. To hold is to suffer longer. To sell is to regret.",
            "Maybe the real profit was the friends we made along the way? No, I prefer USDT.",
            "Time in the market beats timing the market... unless you bought the top.",
            "Chaos is a ladder. But some of us are falling off the ladder.",
            "Every candle tells a story of a battle. Most stories end in silence.",
        ],
        'TRADERS': [
            "You see {name}? This {strategy} dey print money like say na paper. {win_rate}% win rate no be beans.",
            "That {name} na real {strategy}. He just dey wait for the right moment to strike. Professional work.",
            "Omo, {name} is leading the pack. {roi}% ROI? This one na actual wizard.",
            "If you follow {name}, make you get strong heart. That {strategy} lifestyle no be for everybody.",
        ]
    }
    
    # Q&A Style Interludes
    INTERLUDES = [
        ("Wetin dey sup?", "Market dey loading... waittt. Patience is currency."),
        ("Where the money?", "Money dey hide. Find am if you fit."),
        ("Buy or Sell?", "Neither. Sit on your hands before you loose am."),
        ("Is it safe?", "Market is never safe. Use condoms (Stop Loss)."),
        ("Why is it quiet?", "Whales are eating lunch. Don't disturb them."),
        ("When moon?", "When you stop asking and start building."),
        ("Why e red?", "Because you bought. Sell now make e pump."),
        ("Can I short?", "You fit try. But remember, stonks only go up (sometimes)."),
        ("What is the trend?", "The trend is your friend, until it stabs you in the back."),
        ("Should I FOMO?", "If you have to ask, you are already late."),
        ("Who is selling?", "Bogdanoff. He is on the phone right now."),
        ("Is it rug?", "No be rug, na liquidity sweep. No cry."),
        ("Wagmi?", "Maybe. If you survive the night.")
    ]

    @staticmethod
    def get_regime(volatility: float, trend_strength: float, recent_change: float) -> str:
        """
        Determines the 'Vibe' (Regime) based on simple metrics.
        """
        if volatility > 0.8: return 'VOLATILITY'
        
        if abs(recent_change) > 2.0: 
            return 'PUMP' if recent_change > 0 else 'DUMP'
        
        if volatility < 0.2 and trend_strength < 0.2:
            return 'BOREDOM'
            
        if 0.2 <= volatility <= 0.5:
             if trend_strength > 0.5:
                 return 'PUMP' if recent_change > 0 else 'DUMP'
        
        return 'CONFUSION'

    @staticmethod
    def compose(volatility: float = 0.5, trend_strength: float = 0.5, recent_change: float = 0.0) -> Tuple[str, str]:
        """
        Generates a poetic insight and an exclamation.
        Returns: (Narrative, Exclamation)
        """
        regime = PidginPoet.get_regime(volatility, trend_strength, recent_change)
        
        exclamation = random.choice(PidginPoet.EXCLAMATIONS)
        
        # 30% Chance of Q&A
        if random.random() < 0.3:
            q, a = random.choice(PidginPoet.INTERLUDES)
            narrative = f"<b>Q:</b> {q}\n<b>A:</b> <i>{a}</i>"
        elif random.random() < 0.2: # 20% Chance of Trader Commentary (if traders provided later)
            narrative = "Market intelligence flowing..."
        else:
            # 30% Chance to inject "Mood" (Desperation/Philosophy) if regime is dull
            if regime in ['BOREDOM', 'CONFUSION'] and random.random() < 0.3:
                mood = random.choice(['DESPERATION', 'PHILOSOPHY'])
                phrases = PidginPoet.LEXICON.get(mood)
            else:
                phrases = PidginPoet.LEXICON.get(regime, PidginPoet.LEXICON['CONFUSION'])
                
            narrative = random.choice(phrases)
            narrative = f"<i>\"{narrative}\"</i>"
            
        return narrative, exclamation

    @staticmethod
    def get_trader_commentary(trader: dict) -> str:
        """Generates specific commentary for a top trader."""
        phrases = PidginPoet.LEXICON.get('TRADERS', [])
        phrase = random.choice(phrases)
        return phrase.format(
            name=trader.get('name', 'Anon'),
            strategy=trader.get('strategy', 'TRADER'),
            roi=f"{trader.get('roi', 0):.1f}",
            win_rate=f"{trader.get('win_rate', 0):.1f}"
        )

    STRATEGY_LEXICON = {
        'SNIPER': [
            "This guy na Sniper. He dey wait inside bush for 3 days just for one shot. If he shoot, you fit follow am blindly mostly.",
            "Patience master. He no dey rush. He checks confirm before he enter. Copy this one if you hate loosing money.",
            "Sharp shooter logic. He treats capital like egg. Very careful. If you see him buy {symbol}, know say setup clear.",
            "Sniper Rifle Strategy. Low risk, big reward. He is waiting for the perfect headshot on the chart.",
            "Silent killer. He enters market soft, exits loud with profit. If you want peace of mind, shadow this trader.",
            "He observes 90% of the time, executes 10%. Efficiency level: Maximum. Good for copying.",
            "No spray and pray here. One click, one kill. This strategy respects the stop loss but rarely needs it.",
            "Tactical precision. He doesn't chase candles, he lets the price come to his trap.",
            "The disciplined one. He ignores noise. Only trades the signal. Follow him to learn patience.",
            "He treats the market like chess, not casino. CALCULATED moves only."
        ],
        'AGGRESSIVE': [
            "Omo, this one na risk taker! He dey buy dips with full chest. If you get mind, follow am go moon.",
            "High voltage trader. He attacks the market. Win big or go home. Join am but wear helmet.",
            "He sees red candles as discount vouchers. He calls the bottom when others are crying. Bold moves.",
            "No fear for this one eye. He leverage pass normal human being. If {symbol} pumps, he eats big.",
            "Aggressive compounding. He is trying to flip small money to Lambo quick. Risky but sweet if e work.",
            "Volatility surfer. He likes the rough waves. If you want excitement and potential x100, look here.",
            "He fights the bears with bare hands. Contrarian KING. Copy only if you can handle heart attack.",
            "Full throttle. This strategy has no brakes. Accelerating into the breakouts.",
            "He bets on the breakout before it happens. Fortune favors the brave, abi?",
            "Danger is his middle name. High ROI potential but check your blood pressure first."
        ],
        'SCALPER': [
            "Fastest finger in the west. He chop small small everywhere. In-Out-In-Out. Don't blink.",
            "He is scraping crumbs but the crumbs turn to full loaf. High frequency money making.",
            "Machine gun style. Rat-a-tat-tat! 50 trades a day. He collects spread like tax collector.",
            "This one na grinder. He no dey find home run, he just want constant cashflow. Reliable.",
            "Micro moves matter. He turns 0.5% into salary. Copying him requires fast internet.",
            "He milks the market volatility. Up or down, he creates profit. Very active strategy.",
            "Quick reflex. He sees pattern faster than you can say 'buy'. Good for day trading lessons.",
            "Bread and butter trader. Low timeframe warrior. He lives in the 1-minute chart.",
            "Momentum rider for short distance. He hops on the train and hops off before the stop.",
            "Every vibration in price equals money for him. The market heartbeat is his music."
        ],
        'DEFAULT': [
            "Market observer. He is watching the flow. Learning his moves might save you stress.",
            "Balanced approach. Not too hot, not too cold. Just focused on survival and growth.",
            "Mystery strategy. He moves in silence. But the PnL speaks loud.",
            "The Algorithm follower. He trusts the math more than the news. Logic over emotion.",
            "Trend hugger. If the river flows east, he swims east. Go with the flow."
        ]
    }

    @staticmethod
    def get_strategy_description(strategy: str, symbol: str) -> str:
        """
        Generates a Pidgin-style description/TL;DR for a strategy.
        """
        key = strategy if strategy in PidginPoet.STRATEGY_LEXICON else 'DEFAULT'
        options = PidginPoet.STRATEGY_LEXICON[key]
        
        # Salt the random choice with the symbol to make it sticky for a moment if needed,
        # but the user asked for variety, so pure random is better for now.
        desc = random.choice(options)
        
        # Inject symbol if placeholder exists
        return desc.format(symbol=symbol or "market")

