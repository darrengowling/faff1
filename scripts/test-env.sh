#!/bin/bash
# Test Environment Configuration
# Sets environment variables for deterministic E2E testing

export BID_TIMER_SECONDS=8
export ANTI_SNIPE_SECONDS=3
export NEXT_PUBLIC_SOCKET_TRANSPORTS=polling,websocket
export NODE_ENV=test
export PLAYWRIGHT_TEST=true

# Animation and timing overrides for stable tests
export DISABLE_ANIMATIONS=true
export FAST_TIMERS=true

# Test-specific settings
export TEST_TIMEOUT=10000
export TEST_RETRIES=0

echo "🧪 Test environment configured:"
echo "  BID_TIMER_SECONDS=$BID_TIMER_SECONDS"
echo "  ANTI_SNIPE_SECONDS=$ANTI_SNIPE_SECONDS"
echo "  SOCKET_TRANSPORTS=$NEXT_PUBLIC_SOCKET_TRANSPORTS"
echo "  DISABLE_ANIMATIONS=$DISABLE_ANIMATIONS"