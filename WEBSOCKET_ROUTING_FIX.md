# WebSocket Routing Configuration Fix

## Problem Identified
The current Kubernetes ingress configuration routes `/socket.io/*` paths to the frontend service instead of the backend service, preventing WebSocket connections from establishing properly.

## Root Cause
- **Current routing**: `/socket.io/*` → Frontend (port 3000) ❌
- **Correct routing**: `/socket.io/*` → Backend (port 8001) ✅
- **API routing**: `/api/*` → Backend (port 8001) ✅ (already working)

## Solution Options

### Option 1: Kubernetes Ingress Configuration (Recommended)

Apply the provided Kubernetes ingress configuration:

```bash
kubectl apply -f k8s-ingress.yaml
```

This configuration includes:
- Proper WebSocket upgrade headers
- Socket.IO path routing to backend service (port 8001)
- API path routing to backend service (port 8001)
- All other paths to frontend service (port 3000)
- WebSocket-optimized timeouts and buffering settings

### Option 2: Direct Nginx Configuration

If using direct Nginx configuration, apply the provided config:

```bash
# Copy the configuration
cp nginx-ingress-socketio.conf /etc/nginx/conf.d/
# Reload Nginx
nginx -s reload
```

## Key Configuration Elements

### 1. WebSocket Upgrade Headers
```yaml
nginx.ingress.kubernetes.io/proxy-http-version: "1.1"
nginx.ingress.kubernetes.io/proxy-set-header-upgrade: "$http_upgrade"
nginx.ingress.kubernetes.io/proxy-set-header-connection: "upgrade"
```

### 2. WebSocket Timeouts
```yaml
nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
```

### 3. Path Routing Priority
```yaml
# Highest priority: Socket.IO WebSocket
- path: /socket.io
  pathType: Prefix
  backend:
    service:
      name: backend-service
      port:
        number: 8001

# Medium priority: API endpoints  
- path: /api
  pathType: Prefix
  backend:
    service:
      name: backend-service
      port:
        number: 8001

# Lowest priority: Frontend (catch-all)
- path: /
  pathType: Prefix
  backend:
    service:
      name: frontend-service
      port:
        number: 3000
```

## Verification Steps

After applying the configuration:

1. **Test Socket.IO endpoint directly**:
   ```bash
   curl "https://auction-platform-6.preview.emergentagent.com/socket.io/?EIO=4&transport=polling"
   ```
   Should return: `0{"sid":"...","upgrades":["websocket"],"pingInterval":...}`

2. **Test API endpoint** (should still work):
   ```bash
   curl "https://auction-platform-6.preview.emergentagent.com/api/health"
   ```
   Should return: `{"status":"healthy","timestamp":"..."}`

3. **Test WebSocket connection in browser**:
   - Open browser developer tools
   - Navigate to the auction application
   - Check Network tab for successful WebSocket connections
   - Look for `socket.io` connections with status "101 Switching Protocols"

## Expected Results

After applying this fix:

✅ **Socket.IO WebSocket connections** will establish successfully
✅ **Real-time presence tracking** will work (users online/offline)
✅ **Auto-reconnect functionality** will work during network interruptions  
✅ **Live auction updates** will work via WebSocket
✅ **Time synchronization** will work for server-authoritative timing
✅ **All existing API endpoints** will continue working

## Troubleshooting

If the fix doesn't work immediately:

1. **Check ingress controller status**:
   ```bash
   kubectl get ingress ucl-auction-ingress -o yaml
   ```

2. **Check service endpoints**:
   ```bash
   kubectl get svc backend-service frontend-service
   ```

3. **Check ingress controller logs**:
   ```bash
   kubectl logs -n ingress-nginx deployment/nginx-ingress-controller
   ```

4. **Verify WebSocket support**:
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
        "https://auction-platform-6.preview.emergentagent.com/socket.io/"
   ```

## Platform-Specific Notes

- **Emergent Platform**: The platform team may need to apply this ingress configuration
- **Self-Hosted**: Apply using `kubectl apply -f k8s-ingress.yaml`
- **Docker Compose**: Use the nginx configuration file instead

## Impact Assessment

This is a **zero-downtime** configuration change that:
- ✅ Fixes WebSocket routing without affecting existing functionality
- ✅ Maintains all current API endpoints
- ✅ Preserves frontend routing for all web pages
- ✅ Enables real-time features (PR2 and WebSocket-dependent features)

The fix is **backward compatible** and **safe to apply** in production environments.