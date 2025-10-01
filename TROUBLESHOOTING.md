# UCL Auction Troubleshooting Guide

## WebSocket Routing Issues (Platform-Level)

### Symptoms
- WebSocket connections fail to establish
- Real-time features not working (presence, live updates)
- Connection status shows "Reconnecting..." continuously
- Socket.IO endpoint returns HTML instead of WebSocket response

### Root Cause
Ingress configuration routes `/socket.io/*` paths to frontend instead of backend service.

### Solution (For Platform Administrators)
Apply the WebSocket routing configuration provided in `WEBSOCKET_ROUTING_FIX.md`:

```bash
kubectl apply -f k8s-ingress.yaml
```

### Verification
Test Socket.IO endpoint:
```bash
curl "https://livebid-app.preview.emergentagent.com/socket.io/?EIO=4&transport=polling"
```
Should return Socket.IO handshake response, not HTML.

## Connection Issues

### WebSocket Connection Problems

**Symptoms:**
- "Reconnecting..." status showing continuously
- "Offline" status in connection indicator
- Unable to see real-time auction updates
- Presence indicators not updating

**Solutions:**
1. **Check Network Connection**
   - Ensure stable internet connectivity
   - Test with other websites/applications
   - Switch networks if possible (WiFi → Mobile data)

2. **Browser Issues**
   - Refresh the page (Ctrl+F5 or Cmd+R)
   - Clear browser cache and cookies
   - Try incognito/private browsing mode
   - Test in a different browser

3. **Firewall/Proxy Issues**
   - Temporarily disable VPN or proxy
   - Check corporate firewall settings
   - Ensure WebSocket connections are allowed
   - Try from a different network

4. **Server Issues**
   - Check if other users can connect
   - Wait 1-2 minutes for automatic recovery
   - Contact support if widespread issue

### Reconnection Behavior

The system uses exponential backoff for reconnections:
- Attempt 1: 1 second delay
- Attempt 2: 2 second delay  
- Attempt 3: 4 second delay
- Attempt 4: 8 second delay
- Attempts 5+: 10 second delay (maximum)

After 10 failed attempts, manual refresh is required.

## Auction State Issues

### State Not Syncing

**Symptoms:**
- Timer shows incorrect time
- Bids not appearing
- User budgets not updating
- Lot status incorrect

**Solutions:**
1. **Force State Refresh**
   - Disconnect and reconnect to auction
   - Refresh browser page
   - Check connection status indicator

2. **Server Sync Issues**
   - Wait for next heartbeat (30 seconds)
   - Check server time offset in connection health panel
   - Verify WebSocket connection is stable

### Missing Auction Data

**Symptoms:**
- Empty auction room
- No participants showing
- Current lot not loading

**Solutions:**
1. **Authentication Issues**
   - Verify you're logged in correctly
   - Check magic link hasn't expired
   - Ensure league membership is active

2. **Database Issues**
   - Refresh to trigger new data fetch
   - Check browser console for errors
   - Contact admin if persistent

## Presence System Issues

### Users Not Showing Online

**Symptoms:**
- Presence indicators show offline for online users
- Join/leave notifications not appearing
- Participant list incomplete

**Solutions:**
1. **Connection Sync**
   - Refresh the auction page
   - Check if users can see each other's bids
   - Verify WebSocket connection is stable

2. **Multiple Sessions**
   - Ensure only one browser tab per user
   - Close duplicate sessions
   - Clear browser storage if needed

## Performance Issues

### Slow Response Times

**Symptoms:**
- Delayed bid updates
- Slow page loading
- Laggy timer updates

**Solutions:**
1. **Client Performance**
   - Close unnecessary browser tabs
   - Disable browser extensions temporarily
   - Check system resources (RAM, CPU)

2. **Network Performance**
   - Test connection speed
   - Switch to wired connection if on WiFi
   - Contact ISP if speeds are slow

### Memory Issues

**Symptoms:**
- Browser becomes unresponsive
- Page crashes or reloads
- Connection drops frequently

**Solutions:**
1. **Browser Cleanup**
   - Restart browser completely
   - Clear cache and storage
   - Update to latest browser version

2. **System Resources**
   - Close other applications
   - Restart computer if needed
   - Check available RAM

## Error Messages

### "Authentication Failed"
- Magic link expired (links valid for 15 minutes)
- Request new magic link
- Check email for latest link

### "Access Denied"
- League membership required
- Contact league commissioner
- Verify invitation was accepted

### "Auction Not Found"
- Auction may have ended
- Check auction ID in URL
- Contact league admin

### "Connection Lost. Please Refresh"
- Maximum reconnect attempts reached
- Refresh browser page
- Check network connection

## Getting Help

If issues persist after trying these solutions:

1. **Check Browser Console**
   - Press F12 to open developer tools
   - Look for error messages in Console tab
   - Include errors in support request

2. **Connection Health Panel**
   - Note connection status and attempt counts
   - Check server time offset
   - Include in support message

3. **Contact Support**
   - Describe specific symptoms
   - Include browser and device information
   - Mention troubleshooting steps already tried
   - Provide screenshot if helpful

## Advanced Troubleshooting

### WebSocket Debugging

For technical users, check WebSocket connection:

1. Open browser developer tools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Look for socket.io connections
5. Check connection status and messages

### Server Time Sync

If timer issues persist:

1. Check system clock accuracy
2. Verify timezone settings
3. Note server time offset in connection panel
4. Report significant drift (>1 second)

### Connection Health Monitoring

Monitor connection quality:
- Heartbeat response times
- Reconnection frequency
- Presence update accuracy
- State sync timing