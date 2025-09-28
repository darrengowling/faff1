#!/bin/bash

# WebSocket Routing Fix Application Script
# This script applies the Kubernetes ingress configuration to fix WebSocket routing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to test current routing
test_current_routing() {
    log "Testing current WebSocket routing configuration..."
    
    # Test Socket.IO endpoint
    response=$(curl -s -w "%{http_code}" "https://auction-league.preview.emergentagent.com/socket.io/?EIO=4&transport=polling" -o /tmp/socketio_response.txt)
    
    if [ "$response" = "200" ]; then
        content=$(cat /tmp/socketio_response.txt)
        if [[ $content == 0\{* ]]; then
            success "Socket.IO endpoint correctly routes to backend"
            return 0
        elif [[ $content == *"<!doctype html>"* ]]; then
            warning "Socket.IO endpoint incorrectly routes to frontend (HTML returned)"
            return 1
        else
            warning "Socket.IO endpoint returns unexpected content"
            return 1
        fi
    else
        error "Socket.IO endpoint test failed with status: $response"
        return 1
    fi
}

# Function to apply Kubernetes ingress configuration
apply_k8s_ingress() {
    log "Applying Kubernetes ingress configuration..."
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not available. This script requires kubectl access to apply the configuration."
        warning "Please ensure you have kubectl installed and configured with cluster access."
        return 1
    fi
    
    # Check if the ingress file exists
    if [ ! -f "k8s-ingress.yaml" ]; then
        error "k8s-ingress.yaml file not found. Please ensure the file exists in the current directory."
        return 1
    fi
    
    # Apply the configuration
    log "Applying ingress configuration from k8s-ingress.yaml..."
    if kubectl apply -f k8s-ingress.yaml; then
        success "Kubernetes ingress configuration applied successfully"
        
        # Wait for configuration to take effect
        log "Waiting 30 seconds for configuration to take effect..."
        sleep 30
        
        return 0
    else
        error "Failed to apply Kubernetes ingress configuration"
        return 1
    fi
}

# Function to verify the fix
verify_fix() {
    log "Verifying WebSocket routing fix..."
    
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Verification attempt $attempt/$max_attempts..."
        
        if test_current_routing; then
            success "WebSocket routing is working correctly!"
            
            # Additional verification
            log "Running additional verification tests..."
            
            # Test API endpoint still works
            api_response=$(curl -s -w "%{http_code}" "https://auction-league.preview.emergentagent.com/api/health" -o /dev/null)
            if [ "$api_response" = "200" ]; then
                success "API endpoints are still working correctly"
            else
                warning "API endpoints may have issues (status: $api_response)"
            fi
            
            # Test frontend still works
            frontend_response=$(curl -s -w "%{http_code}" "https://auction-league.preview.emergentagent.com/" -o /dev/null)
            if [ "$frontend_response" = "200" ]; then
                success "Frontend is still working correctly"
            else
                warning "Frontend may have issues (status: $frontend_response)"
            fi
            
            success "✅ WebSocket routing fix applied and verified successfully!"
            return 0
        else
            warning "WebSocket routing not yet fixed. Waiting 10 seconds before retry..."
            sleep 10
            ((attempt++))
        fi
    done
    
    error "WebSocket routing fix verification failed after $max_attempts attempts"
    return 1
}

# Function to show manual instructions
show_manual_instructions() {
    warning "If automatic application failed, here are manual steps:"
    echo
    echo "1. Ensure you have kubectl access to the cluster:"
    echo "   kubectl get ingress"
    echo
    echo "2. Apply the ingress configuration:"
    echo "   kubectl apply -f k8s-ingress.yaml"
    echo
    echo "3. Check the ingress status:"
    echo "   kubectl get ingress ucl-auction-ingress -o yaml"
    echo
    echo "4. If using a different ingress setup, use the nginx configuration:"
    echo "   Copy nginx-ingress-socketio.conf to your nginx configuration directory"
    echo
    echo "5. Verify the fix by testing:"
    echo "   curl 'https://auction-league.preview.emergentagent.com/socket.io/?EIO=4&transport=polling'"
    echo "   (Should return Socket.IO handshake, not HTML)"
}

# Main execution
main() {
    log "Starting WebSocket routing fix application..."
    echo
    
    # Step 1: Test current routing
    if test_current_routing; then
        success "WebSocket routing is already working correctly. No fix needed."
        exit 0
    fi
    
    warning "WebSocket routing issue confirmed. Proceeding with fix..."
    echo
    
    # Step 2: Apply Kubernetes ingress configuration
    if apply_k8s_ingress; then
        # Step 3: Verify the fix
        if verify_fix; then
            success "🎉 WebSocket routing fix completed successfully!"
            echo
            success "Real-time features should now work:"
            success "  ✅ Socket.IO connections"
            success "  ✅ User presence tracking"  
            success "  ✅ Auto-reconnect functionality"
            success "  ✅ Live auction updates"
            exit 0
        else
            error "Fix application succeeded but verification failed."
            show_manual_instructions
            exit 1
        fi
    else
        error "Failed to apply Kubernetes ingress configuration."
        show_manual_instructions
        exit 1
    fi
}

# Check if running with help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "WebSocket Routing Fix Application Script"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "This script fixes the WebSocket routing issue by applying the correct"
    echo "Kubernetes ingress configuration to route /socket.io/* paths to the"
    echo "backend service instead of the frontend service."
    echo
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo "  --test-only   Only test current routing, don't apply changes"
    echo
    echo "Prerequisites:"
    echo "  - kubectl must be installed and configured"
    echo "  - k8s-ingress.yaml must exist in current directory"
    echo "  - Cluster admin access may be required"
    echo
    exit 0
fi

# Check if running in test-only mode
if [[ "$1" == "--test-only" ]]; then
    log "Running in test-only mode..."
    test_current_routing
    exit $?
fi

# Run main function
main