#!/usr/bin/env python3
"""
Fix auction nomination order for testing
"""

import asyncio
import sys
sys.path.append('/app/backend')
from database import db, initialize_database

async def fix_auction_nomination_order(league_id):
    """Fix the nomination order for an auction"""
    await initialize_database()
    
    # Get league members
    members = await db.league_memberships.find({"league_id": league_id}).to_list(length=None)
    user_ids = [member["user_id"] for member in members]
    
    print(f"Found {len(user_ids)} members: {user_ids}")
    
    # Update auction with nomination order
    result = await db.auctions.update_one(
        {"_id": league_id},  # Auction ID is same as league ID
        {"$set": {"nomination_order": user_ids}}
    )
    
    print(f"Updated auction nomination order: {result.modified_count} documents modified")
    
    # Verify the update
    auction = await db.auctions.find_one({"_id": league_id})
    if auction:
        print(f"Auction nomination order: {auction.get('nomination_order', [])}")
    else:
        print("Auction not found")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_auction_nomination.py <league_id>")
        sys.exit(1)
    
    league_id = sys.argv[1]
    asyncio.run(fix_auction_nomination_order(league_id))