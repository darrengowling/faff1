#!/usr/bin/env python3
"""
UCL Auction Demo Seed Script
Creates a complete demo environment with:
- UCL clubs
- Demo league with 4 managers
- Pre-populated auction
- Sample results and scoring
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.append('/app/backend')

from database import initialize_database, db
from models import *
from models import LotStatus
from league_service import LeagueService
from auction_engine import AuctionEngine
from scoring_service import ScoringService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UCLAuctionSeeder:
    def __init__(self):
        self.demo_managers = [
            {"email": "alice.manager@demo.com", "display_name": "Alice Thompson", "password": "demo123"},
            {"email": "bob.manager@demo.com", "display_name": "Bob Rodriguez", "password": "demo123"}, 
            {"email": "carol.manager@demo.com", "display_name": "Carol Chen", "password": "demo123"},
            {"email": "david.manager@demo.com", "display_name": "David Kumar", "password": "demo123"}
        ]
        self.commissioner_email = "commissioner@demo.com"
        self.demo_league_id = None
        self.demo_auction_id = None
        self.club_ids = {}
        self.user_ids = {}
        
    async def run_seeding(self):
        """Run the complete seeding process"""
        try:
            logger.info("🚀 Starting UCL Auction Demo Seeding...")
            
            # Initialize database
            await initialize_database()
            
            # Step 1: Load and create clubs
            await self.seed_clubs()
            
            # Step 2: Create demo users
            await self.create_demo_users()
            
            # Step 3: Create demo league
            await self.create_demo_league()
            
            # Step 4: Set up auction
            await self.setup_auction()
            
            # Step 5: Simulate auction bidding
            await self.simulate_auction()
            
            # Step 6: Load fixtures
            await self.seed_fixtures()
            
            # Step 7: Process sample results
            await self.process_sample_results()
            
            # Step 8: Generate summary
            await self.generate_summary()
            
            logger.info("✅ Demo seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Seeding failed: {e}")
            raise

    async def seed_clubs(self):
        """Load clubs from JSON and insert into database"""
        logger.info("📚 Seeding UCL clubs...")
        
        clubs_file = Path("/app/seed_data/clubs.json")
        with open(clubs_file, 'r') as f:
            clubs_data = json.load(f)
        
        # Clear existing clubs
        await db.clubs.delete_many({})
        
        for club_data in clubs_data:
            club = Club(**club_data)
            club_dict = club.model_dump(by_alias=True)
            result = await db.clubs.insert_one(club_dict)
            self.club_ids[club_data["ext_ref"]] = result.inserted_id
            
        logger.info(f"✅ Seeded {len(clubs_data)} clubs")

    async def create_demo_users(self):
        """Create demo users including commissioner"""
        logger.info("👥 Creating demo users...")
        
        # Clear existing users
        await db.users.delete_many({"email": {"$regex": "@demo\\.com$"}})
        
        # Create commissioner
        commissioner = User(
            email=self.commissioner_email,
            display_name="Demo Commissioner",
            verified=True
        )
        comm_dict = commissioner.model_dump(by_alias=True)
        result = await db.users.insert_one(comm_dict)
        self.user_ids["commissioner"] = result.inserted_id
        
        # Create managers
        for i, manager_data in enumerate(self.demo_managers):
            user = User(
                email=manager_data["email"],
                display_name=manager_data["display_name"],
                verified=True
            )
            user_dict = user.model_dump(by_alias=True)
            result = await db.users.insert_one(user_dict)
            self.user_ids[f"manager_{i}"] = result.inserted_id
            
        logger.info(f"✅ Created {len(self.demo_managers) + 1} demo users")

    async def create_demo_league(self):
        """Create demo league with commissioner and managers"""
        logger.info("🏆 Creating demo league...")
        
        # Create league using LeagueService
        league_create = LeagueCreate(
            name="UCL Demo League 2025-26",
            season="2025-26",
            settings=LeagueSettings(
                budget_per_manager=100,
                min_increment=1,
                club_slots_per_manager=3,
                anti_snipe_seconds=30,
                bid_timer_seconds=60,
                max_managers=8,
                min_managers=4,
                scoring_rules=ScoringRulePoints(
                    club_goal=1,
                    club_win=3,
                    club_draw=1
                )
            )
        )
        
        league_response = await LeagueService.create_league_with_setup(
            league_create, 
            self.user_ids["commissioner"]
        )
        self.demo_league_id = league_response.id
        
        # Add managers to league
        for i in range(len(self.demo_managers)):
            user_id = self.user_ids[f"manager_{i}"]
            
            # Create membership
            membership = Membership(
                league_id=self.demo_league_id,
                user_id=user_id,
                role=MembershipRole.MANAGER
            )
            await db.memberships.insert_one(membership.model_dump(by_alias=True))
            
            # Create roster
            roster = Roster(
                league_id=self.demo_league_id,
                user_id=user_id,
                budget_start=100,
                budget_remaining=100,
                club_slots=3
            )
            await db.rosters.insert_one(roster.model_dump(by_alias=True))
            
        # Update league member count
        await db.leagues.update_one(
            {"_id": self.demo_league_id},
            {"$set": {"member_count": 5, "status": "ready"}}
        )
        
        logger.info(f"✅ Created demo league: {self.demo_league_id}")

    async def setup_auction(self):
        """Set up auction with lots"""
        logger.info("🔨 Setting up auction...")
        
        # Get auction for the league
        auction = await db.auctions.find_one({"league_id": self.demo_league_id})
        if auction:
            self.demo_auction_id = auction["_id"]
            
            # Create lots for first 8 clubs (2 per manager for bidding)
            club_ext_refs = list(self.club_ids.keys())[:8]
            
            for i, club_ext_ref in enumerate(club_ext_refs):
                club_id = self.club_ids[club_ext_ref]
                
                # Assign nominator in round-robin fashion
                nominator_id = self.user_ids[f"manager_{i % 4}"]
                
                lot = Lot(
                    auction_id=self.demo_auction_id,
                    club_id=club_id,
                    nominated_by=nominator_id,
                    order_index=i,
                    current_bid=0,
                    status=LotStatus.PENDING
                )
                await db.lots.insert_one(lot.model_dump(by_alias=True))
                
            logger.info(f"✅ Created {len(club_ext_refs)} lots for auction")
        else:
            logger.error("❌ No auction found for demo league")

    async def simulate_auction(self):
        """Simulate auction bidding to create realistic ownership"""
        logger.info("🎪 Simulating auction bidding...")
        
        if not self.demo_auction_id:
            logger.error("❌ No auction ID available")
            return
            
        # Predefined bidding results for demo
        auction_results = [
            {"club_ext": "UEFA-MCI", "winner": "manager_0", "price": 25},
            {"club_ext": "UEFA-RMA", "winner": "manager_1", "price": 30}, 
            {"club_ext": "UEFA-BAR", "winner": "manager_2", "price": 28},
            {"club_ext": "UEFA-BAY", "winner": "manager_3", "price": 22},
            {"club_ext": "UEFA-PSG", "winner": "manager_0", "price": 20},
            {"club_ext": "UEFA-LIV", "winner": "manager_1", "price": 26},
            {"club_ext": "UEFA-ARS", "winner": "manager_2", "price": 18},
            {"club_ext": "UEFA-INT", "winner": "manager_3", "price": 15}
        ]
        
        for result in auction_results:
            club_id = self.club_ids[result["club_ext"]]
            winner_id = self.user_ids[result["winner"]]
            price = result["price"]
            
            # Create roster club (ownership)
            roster_club = RosterClub(
                roster_id=f"roster_{winner_id}_{self.demo_league_id}",
                league_id=self.demo_league_id,
                user_id=winner_id,
                club_id=club_id,
                price=price
            )
            await db.roster_clubs.insert_one(roster_club.model_dump(by_alias=True))
            
            # Update roster budget
            await db.rosters.update_one(
                {"league_id": self.demo_league_id, "user_id": winner_id},
                {"$inc": {"budget_remaining": -price}}
            )
            
            # Update lot status
            await db.lots.update_one(
                {"auction_id": self.demo_auction_id, "club_id": club_id},
                {"$set": {
                    "status": "sold",
                    "winner_id": winner_id,
                    "final_price": price,
                    "current_bid": price
                }}
            )
            
        logger.info(f"✅ Simulated auction with {len(auction_results)} club sales")

    async def seed_fixtures(self):
        """Load fixtures from JSON"""
        logger.info("📅 Seeding fixtures...")
        
        fixtures_file = Path("/app/seed_data/fixtures.json")
        with open(fixtures_file, 'r') as f:
            fixtures_data = json.load(f)
        
        # Clear existing fixtures for demo league
        await db.fixtures.delete_many({"league_id": self.demo_league_id})
        
        for fixture_data in fixtures_data:
            # Parse date string to datetime
            date_str = fixture_data["date"]
            parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            fixture = Fixture(
                league_id=self.demo_league_id,
                match_id=fixture_data["match_id"],
                season=fixture_data["season"],
                date=parsed_date,
                home_ext=fixture_data["home_ext"],
                away_ext=fixture_data["away_ext"],
                status=fixture_data["status"]
            )
            await db.fixtures.insert_one(fixture.model_dump(by_alias=True))
            
        logger.info(f"✅ Seeded {len(fixtures_data)} fixtures")

    async def process_sample_results(self):
        """Process sample match results to generate scoring"""
        logger.info("⚽ Processing sample results...")
        
        results_file = Path("/app/seed_data/results_sample.json")
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        # Clear existing results for demo league
        await db.result_ingest.delete_many({"league_id": self.demo_league_id})
        await db.weekly_points.delete_many({"league_id": self.demo_league_id})
        await db.settlements.delete_many({"league_id": self.demo_league_id})
        
        processed_count = 0
        for result_data in results_data:
            try:
                # Update result with demo league ID
                result_data["league_id"] = self.demo_league_id
                
                # Parse kicked_off_at
                kicked_off_str = result_data["kicked_off_at"]
                kicked_off_at = datetime.fromisoformat(kicked_off_str.replace('Z', '+00:00'))
                
                # Process result using ScoringService
                result = await ScoringService.ingest_result(
                    league_id=self.demo_league_id,
                    match_id=result_data["match_id"],
                    season=result_data["season"],
                    home_ext=result_data["home_ext"],
                    away_ext=result_data["away_ext"],
                    home_goals=result_data["home_goals"],
                    away_goals=result_data["away_goals"],
                    kicked_off_at=kicked_off_at,
                    status=result_data["status"]
                )
                
                if result["success"]:
                    processed_count += 1
                else:
                    logger.warning(f"Failed to process result for {result_data['match_id']}: {result['message']}")
                    
            except Exception as e:
                logger.error(f"Error processing result {result_data['match_id']}: {e}")
                
        logger.info(f"✅ Processed {processed_count} match results")

    async def generate_summary(self):
        """Generate demo summary information"""
        logger.info("📊 Generating demo summary...")
        
        # Get league standings
        standings = await ScoringService.get_league_standings(self.demo_league_id)
        
        # Get club ownership summary
        ownership = await db.roster_clubs.find({"league_id": self.demo_league_id}).to_list(length=None)
        
        # Get total points
        points_data = await db.weekly_points.find({"league_id": self.demo_league_id}).to_list(length=None)
        total_points = sum(p["points_delta"] for p in points_data)
        
        summary = {
            "demo_league_id": self.demo_league_id,
            "demo_auction_id": self.demo_auction_id,
            "commissioner_email": self.commissioner_email,
            "manager_emails": [m["email"] for m in self.demo_managers],
            "clubs_seeded": len(self.club_ids),
            "clubs_owned": len(ownership),
            "total_points_awarded": total_points,
            "fixtures_loaded": await db.fixtures.count_documents({"league_id": self.demo_league_id}),
            "results_processed": await db.result_ingest.count_documents({"league_id": self.demo_league_id}),
            "standings_preview": standings[:3] if standings else []
        }
        
        # Save summary to file
        with open("/app/demo_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
            
        logger.info("=" * 60)
        logger.info("🎉 UCL AUCTION DEMO READY!")
        logger.info("=" * 60)
        logger.info(f"📧 Commissioner: {self.commissioner_email}")
        logger.info(f"📧 Managers: {', '.join([m['email'] for m in self.demo_managers])}")
        logger.info(f"🏆 League ID: {self.demo_league_id}")
        logger.info(f"⚽ Clubs: {len(self.club_ids)} seeded, {len(ownership)} owned")
        logger.info(f"📊 Points: {total_points} total points from {len(points_data)} scoring events")
        logger.info(f"📅 Fixtures: {await db.fixtures.count_documents({'league_id': self.demo_league_id})} loaded")
        logger.info(f"⚽ Results: {await db.result_ingest.count_documents({'league_id': self.demo_league_id})} processed")
        logger.info("=" * 60)
        logger.info("🔗 Demo URLs:")
        logger.info("   - Login: https://realtime-socket-fix.preview.emergentagent.com")
        logger.info(f"   - League: https://realtime-socket-fix.preview.emergentagent.com/dashboard")
        logger.info("=" * 60)

async def main():
    """Main seeding function"""
    seeder = UCLAuctionSeeder()
    await seeder.run_seeding()

if __name__ == "__main__":
    asyncio.run(main())