#!/bin/bash

# Apply Socket.IO Ingress Configuration
# This script applies the updated Kubernetes ingress configuration

echo "🔧 Applying Socket.IO Ingress Configuration..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not available. This script should be run where kubectl is configured."
    echo "💡 Please manually apply the k8s-ingress.yaml configuration:"
    echo "   kubectl apply -f k8s-ingress.yaml"
    exit 1
fi

# Apply the ingress configuration
echo "📄 Applying k8s-ingress.yaml..."
kubectl apply -f k8s-ingress.yaml

# Check ingress status
echo "🔍 Checking ingress status..."
kubectl get ingress ucl-auction-ingress -o wide

echo "✅ Ingress configuration applied!"
echo ""
echo "🧪 Test Socket.IO routing:"
echo "   curl -I https://livebid-app.preview.emergentagent.com/socket.io/"
echo "   (Should return Socket.IO handshake, not HTML)"