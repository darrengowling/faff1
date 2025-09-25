#!/bin/bash

echo "🚀 Starting UCL Auction Demo Seeding..."
echo "=================================="

# Change to app directory
cd /app

# Set Python path
export PYTHONPATH="/app/backend:$PYTHONPATH"

# Run the seed script
python3 seed_script.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Seeding completed successfully!"
    echo ""
    echo "📋 Demo Summary:"
    if [ -f "demo_summary.json" ]; then
        cat demo_summary.json
    fi
    echo ""
    echo "🔗 Next Steps:"
    echo "1. Visit: https://pifa-friends.preview.emergentagent.com"
    echo "2. Use magic-link login with any demo email:"
    echo "   - commissioner@demo.com (Commissioner access)"
    echo "   - alice.manager@demo.com (Manager)"
    echo "   - bob.manager@demo.com (Manager)"
    echo "   - carol.manager@demo.com (Manager)"
    echo "   - david.manager@demo.com (Manager)"
    echo ""
else
    echo "❌ Seeding failed!"
    exit 1
fi