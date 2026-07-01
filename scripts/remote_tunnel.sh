#!/bin/bash
# remote_tunnel.sh - Easily switch between local and remote LGNN nodes

REMOTE_IP="141.147.20.191"
REMOTE_USER="ubuntu"
PORT=8001

echo "👁️  Aethelnet Remote Tunnel Controller"
echo "======================================"

# 1. Check if local backend service is running and stop it
if systemctl --user is-active --quiet aethelnet-node.service; then
    echo "⚠️  Local aethelnet-node service is active on port $PORT."
    echo "🛑 Stopping local service to clear the port..."
    systemctl --user stop aethelnet-node.service
    WAS_ACTIVE=true
else
    echo "✅ Local port $PORT is clear."
    WAS_ACTIVE=false
fi

# 2. Establish SSH Tunnel
echo "🌐 Spawning SSH Tunnel to $REMOTE_USER@$REMOTE_IP..."
echo "📊 Forwarding remote port $PORT to local port $PORT"
echo "⚡ Press Ctrl+C to close the tunnel and restore local node"
echo ""

ssh -N -L $PORT:localhost:$PORT $REMOTE_USER@$REMOTE_IP

# 3. Restore local service if it was active before
echo ""
echo "🛑 Tunnel closed."
if [ "$WAS_ACTIVE" = true ]; then
    echo "🚀 Restarting local aethelnet-node service..."
    systemctl --user start aethelnet-node.service
    echo "✅ Local service active."
fi
