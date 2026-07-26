class BotStrings:
    # --- SYSTEM ---
    WELCOME_MESSAGE = (
        "<b>AURATIC</b> <i>Market Intelligence</i>\n"
        "<code>════════════════════════════════</code>\n\n"
        "[+] <b>ML-powered trading signals</b>\n"
        "[~] <b>Real-time market analysis</b>\n"
        "[*] <b>Crypto, Forex, Stocks & Commodities</b>\n\n"
        "<b>QUICK START</b>\n"
        "• Type any symbol: <code>BTC ETH GOLD SPX</code>\n"
        "• Access Manual: <code>/help</code> or <code>/commands</code>\n"
        "• Or use the buttons below\n\n"
        "<code>════════════════════════════════</code>\n"
        "<i>Free signals • Tips welcome</i>"
    )

    HELP_WARREN = (
        "<b>1. PHILOSOPHY</b>\nValue Investing. Long horizons. Ignore the noise.\n"
        "We seek assets trading below their intrinsic value.\n\n"
        "<b>2. STRATEGY</b>\n"
        "• Buy when fear is high (Low RSI, Panic Regime).\n"
        "• Hold through volatility.\n"
        "• Focus on fundamentals, not ticks."
    )

    HELP_QUANT = (
        "<b>1. PHILOSOPHY</b>\nHigh Frequency. Statistical Arbitrage. Precision.\n"
        "We exploit inefficient pricing in microseconds.\n\n"
        "<b>2. MECHANICS</b>\n"
        "• Z-Score Mean Reversion.\n"
        "• Volatility Clustering breakdown.\n"
        "• Order Flow imbalance."
    )

    HELP_CORE = (
        "<b>1. OPERATIONAL WORKFLOW</b>\n"
        "• Scan: <code>/scan</code> uses ML to find divergence.\n"
        "• Verify: <code>/stats [SYM]</code> checks if multiple models align.\n\n"
        "<b>2. INTERNAL MECHANICS (ML)</b>\n"
        "• Reservoir Computing (ESN): Analyzing chaotic time-series.\n"
        "• Regime Detection (GMM): Classify market state (Calm, Volatile, Crash).\n"
        "• Z-Score Flux: Deviation > 2.0σ precedes snap-back."
    )

    HELP_SIMPLE = (
        "<b>1. PRICE [INTEL]</b>\nCheck pulse & browse universe. Type symbols like <code>BTC</code>.\n\n"
        "<b>2. PERFORMANCE [SCAN]</b>\nML detects opportunities.\n\n"
        "<b>3. EVENTS & NEWS</b>\nReal-time market shocks."
    )

    RISK_USAGE = (
        "<b>[ RISK MANAGEMENT PARADIGM ]</b>\n"
        "• Position Size: <code>{size:.1f}%</code>\n"
        "• Stop Loss:     <code>{stop:.1f}%</code>\n"
        "• Profit Target: <code>{target:.1f}%</code>\n\n"
        "<b>USAGE:</b>\n"
        "<code>/risk size 0.05</code>\n"
        "<code>/risk stop 0.02</code>\n"
        "<code>/risk target 0.10</code>"
    )

    SECURITY_AUDIT = (
        "<b>[ SECURITY AUDIT ]</b>\n"
        "Protocol: <code>PHOENIX_PRIME</code>\n\n"
        "<b>[ NETWORK ]</b>\n"
        "> External IP: <code>{ip}</code>\n"
        "> Cloud Mesh: {swarm_mesh}\n"
        "  (Action: Verify Whitelist Match)\n\n"
        "<b>[ CREDENTIALS ]</b>\n"
        "> API Config: {status_badge}\n"
        "> Environment: {env_mode_str}\n\n"
        "<b>[ CONNECTIVITY ]</b>\n"
        "> Binance Link: {binance_link}\n"
        "> Alpaca Link : {alpaca_status}\n\n"
        "<b>[ SWARM INTELLIGENCE ]</b>\n"
        "{swarm_details}\n\n"
        "<b>[ DIAGNOSTICS MATRIX ]</b>\n"
        "{diag_env} Env Conflict (Prod vs Testnet)\n"
        "{diag_creds} Missing Credentials\n"
        "{diag_ip} IP Whitelist / API Permissions\n\n"
        "<b>[ MAINTENANCE PROTOCOLS ]</b>\n"
        "{maintenance_action}\n\n"
        "> Review 'Diagnostic Matrix' to identify root cause.\n"
        "> Trading Mode: SPOT\n"
        "> Execution: ENABLED"
    )

    # --- MARKET ---
    PRICE_LANDING_HEADER = (
        "<b>[ PRICE INTELLIGENCE LANDING ]</b>\n"
        "<code>// TELEMETRY_FOUNDATION_READY</code>\n\n"
    )
    
    PRICE_LANDING_FOOTER = (
        "\n<b>[ OPERATIVE TIPS ]</b>\n"
        "• Use <code>/price [SYM]</code> for specific data.\n"
        "• Hint: Type any symbol (e.g. BTC) for an instant ticker.\n\n"
        "<code>══════════════════════════════</code>\n"
        "<b>[ STATUS: OPERATIONAL ]</b>"
    )

    CLUSTER_HEADER = (
        "<b>[ {cluster} CLUSTER ]</b>\n"
        "<code>TREND: {trend} | AVG: {avg_change:+.2f}%</code>\n"
        "<code>══════════════════════════════</code>\n\n"
        "<b>MEMBERS</b>\n"
    )

    SESSION_TEMPLATE = (
        "<b>[ {name} SESSION ]</b>\n"
        "<code>STATUS: {status}</code>\n"
        "<code>{exchanges}</code>\n"
        "<code>HOURS: {hours}</code>\n"
        "<code>══════════════════════════</code>\n\n"
        "<b>KEY INSTRUMENTS</b>\n"
    )

    CALENDAR_HEADER = (
        "<b>[ {title} ]</b>\n"
        "<code>══════════════════════════</code>\n\n"
    )
