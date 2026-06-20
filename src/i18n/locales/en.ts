export default {
    nodes: {
        types: {
            market: "Market Hub",
            symbol: "Trading Pair",
            cluster: "Asset Cluster",
            event: "Market Event",
            singularity: "The Singularity",
            news: "Breaking News"
        },
        tldr: {
            market: "{{name}} is a central hub aggregating liquidity and sentiment for the entire sector.",
            symbol: "{{name}} is a tradable asset currently priced at {{price}}. Detection confidence is {{confidence}}%.",
            cluster: "{{name}} represents a group of highly correlated assets moving in unison.",
            event: "Major market event '{{name}}' detected. Volatility expected to increase.",
            singularity: "The Origin Point. All market data flows from here."
        },
        details: {
            rsi: "Relative Strength Index (14). Measures momentum.",
            drift: "Price Drift. Immediate short-term trend direction.",
            turbulence: "Market Turbulence. Measure of chaotic volatility.",
            sentiment: "AI Sentiment Analysis based on global data streams."
        }
    },
    ui: {
        pins: {
            title: "Pinned Items",
            subtitle: "Click the pin icon on any item to track it here",
            pin: "Pin Node",
            unpin: "Unpin Node",
            empty: "No items pinned yet",
            tooltip: {
                pinned: "Pinned to dashboard",
                unpinned: "Click to pin this item"
            }
        },
        galaxy: {
            focus: "Focus Mode",
            reset: "Reset View",
            layers: "Layers"
        },
        actions: {
            expand: "Expand Details",
            collapse: "Collapse",
            close: "Close Panel",
            connect: "Connect"
        },
        connections: {
            title: "Connections",
            more: "+{{count}} more"
        },
        summary: {
            export: "Copy to Clipboard",
            refresh: "Refresh All",
            clear: "Clear All",
            header: "Your personal watchlist",
            copied: "✅ Copied to clipboard!",
            updated: "Updated {{time}}"
        },
        time: {
            now: "just now",
            sec: "{{count}}s ago",
            min: "{{count}}m ago",
            hour: "{{count}}h ago",
            day: "{{count}}d ago"
        }
    }
}
