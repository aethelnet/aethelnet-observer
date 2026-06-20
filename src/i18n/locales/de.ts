export default {
    nodes: {
        types: {
            market: "Marktplatz",
            symbol: "Handelspaar",
            cluster: "Asset-Cluster",
            event: "Marktereignis",
            singularity: "Die Singularität",
            news: "Eilmeldung"
        },
        tldr: {
            market: "{{name}} ist ein zentraler Knotenpunkt, der Liquidität und Stimmung für den gesamten Sektor bündelt.",
            symbol: "{{name}} ist ein handelbarer Vermögenswert mit einem aktuellen Preis von {{price}}. Erkennungsgenauigkeit: {{confidence}}%.",
            cluster: "{{name}} repräsentiert eine Gruppe hochkorrelierter Vermögenswerte, die sich im Einklang bewegen.",
            event: "Großes Marktereignis '{{name}}' erkannt. Erhöhte Volatilität erwartet.",
            singularity: "Der Ursprungspunkt. Alle Marktdaten fließen von hier."
        },
        details: {
            rsi: "Relative Stärke Index (14). Misst das Momentum.",
            drift: "Preisdrift. Unmittelbare kurzfristige Trendrichtung.",
            turbulence: "Marktturbulenz. Maß für chaotische Volatilität.",
            sentiment: "KI-Stimmungsanalyse basierend auf globalen Datenströmen."
        }
    },
    ui: {
        pins: {
            title: "Angepinnte Elemente",
            subtitle: "Klicken Sie auf das Pin-Symbol, um ein Element hier zu verfolgen",
            pin: "Anpinnen",
            unpin: "Lösen",
            empty: "Noch keine Elemente angepinnt",
            tooltip: {
                pinned: "Auf Dashboard angepinnt",
                unpinned: "Klicken zum Anpinnen"
            }
        },
        galaxy: {
            focus: "Fokus-Modus",
            reset: "Ansicht zurücksetzen",
            layers: "Ebenen"
        },
        actions: {
            expand: "Details erweitern",
            collapse: "Einklappen",
            close: "Schließen",
            connect: "Verbinden"
        },
        connections: {
            title: "Verbindungen",
            more: "+{{count}} weitere"
        },
        summary: {
            export: "In Zwischenablage kopieren",
            refresh: "Alles aktualisieren",
            clear: "Alles löschen",
            header: "Ihre persönliche Watchlist",
            copied: "✅ In Zwischenablage kopiert!",
            updated: "Aktualisiert {{time}}"
        },
        time: {
            now: "gerade eben",
            sec: "vor {{count}}s",
            min: "vor {{count}}m",
            hour: "vor {{count}}h",
            day: "vor {{count}}d"
        }
    }
}
