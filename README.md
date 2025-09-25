# UCL Auction Application

A real-time auction system for Champions League clubs with robust connection management and presence tracking.

## Connection & Presence System

The UCL Auction application includes robust WebSocket connection management with automatic reconnection and real-time presence tracking.

### Connection Features

- **Auto-Reconnect**: Exponential backoff reconnection (1s → 2s → 4s → 8s → 10s max)
- **Connection Status**: Real-time connection indicator in the UI
- **State Restoration**: Server snapshots restore auction state on reconnect
- **Presence Tracking**: See who's online/offline in real-time
- **Heartbeat System**: Maintains connection health with 30s intervals

### Connection Indicators

- 🟢 **Connected**: Normal operation
- 🔵 **Connecting**: Initial connection attempt
- 🟡 **Reconnecting**: Attempting to restore connection
- 🔴 **Offline**: Connection failed (refresh required)

### Troubleshooting Connections

If you experience connection issues:

1. **Check your internet connection**
2. **Refresh the browser page**
3. **Disable VPN or proxy temporarily**
4. **Try a different browser or incognito mode**
5. **Check if other users can connect**

**For Platform Administrators**: If WebSocket connections fail consistently, see `WEBSOCKET_ROUTING_FIX.md` for ingress configuration updates that route `/socket.io/*` paths to the backend service (port 8001).

The system automatically handles temporary disconnections and will restore your auction state when reconnected.

## Testing

Run the test suite with:
```bash
npm test
pytest test_reconnect_presence.py -v
```
