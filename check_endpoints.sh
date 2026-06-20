#!/bin/bash
# Quick script to check what endpoints the backend actually has

echo "🔍 Checking backend API endpoints..."
echo ""

BASE="http://localhost:8000"

echo "📋 Available endpoints (from OpenAPI spec):"
curl -s "$BASE/openapi.json" 2>/dev/null | \
    python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"  {method.upper():6} {path}\") for path, methods in data.get('paths', {}).items() for method in methods.keys()]" 2>/dev/null || \
    echo "  (Could not parse OpenAPI spec)"

echo ""
echo "🧪 Testing common endpoints:"
for endpoint in "/" "/api/metrics" "/metrics" "/api/v1/metrics" "/api/performance" "/api/stats"; do
    response=$(curl -s -w "\n%{http_code}" "$BASE$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -1)
    
    if [ "$http_code" = "200" ]; then
        echo "  ✅ $endpoint (200) - $body" | head -c 80
        echo ""
    elif [ "$http_code" != "404" ]; then
        echo "  ⚠️  $endpoint ($http_code)"
    fi
done

echo ""
echo "📖 Full API docs: $BASE/docs"







