"""
Competition Profile Service
Handles competition profile management and league creation with defaults
"""

import logging
from typing import List, Optional, Dict
from models import CompetitionProfile, CompetitionProfileResponse, LeagueSettings, LeagueSize, ScoringRulePoints
from database import db

logger = logging.getLogger(__name__)

class CompetitionService:
    """Service for managing competition profiles and applying defaults"""
    
    @staticmethod
    async def get_all_profiles() -> List[CompetitionProfileResponse]:
        """Get all available competition profiles"""
        try:
            profiles = await db.competition_profiles.find({}).to_list(length=None)
            return [
                CompetitionProfileResponse(
                    id=profile["_id"],
                    competition=profile["competition"],
                    short_name=profile["short_name"],
                    defaults=profile["defaults"],
                    description=profile.get("description")
                )
                for profile in profiles
            ]
        except Exception as e:
            logger.error(f"Failed to get competition profiles: {e}")
            return []
    
    @staticmethod
    async def get_profile_by_id(profile_id: str) -> Optional[CompetitionProfileResponse]:
        """Get specific competition profile by ID"""
        try:
            profile = await db.competition_profiles.find_one({"_id": profile_id})
            if profile:
                return CompetitionProfileResponse(
                    id=profile["_id"],
                    competition=profile["competition"],
                    short_name=profile["short_name"],
                    defaults=profile["defaults"],
                    description=profile.get("description")
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get competition profile {profile_id}: {e}")
            return None
    
    @staticmethod
    async def get_default_settings(profile_id: str = "ucl") -> LeagueSettings:
        """Get default league settings from competition profile"""
        try:
            profile = await db.competition_profiles.find_one({"_id": profile_id})
            if profile and "defaults" in profile:
                defaults = profile["defaults"]
                
                # Convert to LeagueSettings model
                return LeagueSettings(
                    budget_per_manager=defaults.get("budget_per_manager", 100),
                    min_increment=defaults.get("min_increment", 1),
                    club_slots_per_manager=defaults.get("club_slots", 3),
                    anti_snipe_seconds=defaults.get("anti_snipe_seconds", 30),
                    bid_timer_seconds=defaults.get("bid_timer_seconds", 60),
                    league_size=LeagueSize(
                        min=defaults.get("league_size", {}).get("min", 2),
                        max=defaults.get("league_size", {}).get("max", 8)
                    ),
                    scoring_rules=ScoringRulePoints(
                        club_goal=defaults.get("scoring_rules", {}).get("club_goal", 1),
                        club_win=defaults.get("scoring_rules", {}).get("club_win", 3),
                        club_draw=defaults.get("scoring_rules", {}).get("club_draw", 1)
                    )
                )
            else:
                # Return default UCL settings if profile not found
                return LeagueSettings(
                    budget_per_manager=100,
                    min_increment=1,
                    club_slots_per_manager=3,
                    anti_snipe_seconds=30,
                    bid_timer_seconds=60,
                    league_size=LeagueSize(min=2, max=8),
                    scoring_rules=ScoringRulePoints(club_goal=1, club_win=3, club_draw=1)
                )
                
        except Exception as e:
            logger.error(f"Failed to get default settings: {e}")
            # Return safe defaults
            return LeagueSettings(
                budget_per_manager=100,
                min_increment=1,
                club_slots_per_manager=3,
                anti_snipe_seconds=30,
                bid_timer_seconds=60,
                league_size=LeagueSize(min=4, max=8),
                scoring_rules=ScoringRulePoints(club_goal=1, club_win=3, club_draw=1)
            )
    
    @staticmethod
    async def create_profile(profile_data: Dict) -> CompetitionProfileResponse:
        """Create a new competition profile"""
        try:
            profile = CompetitionProfile(**profile_data)
            profile_dict = profile.model_dump(by_alias=True)
            
            result = await db.competition_profiles.insert_one(profile_dict)
            
            return CompetitionProfileResponse(
                id=result.inserted_id,
                competition=profile.competition,
                short_name=profile.short_name,
                defaults=profile.defaults,
                description=profile.description
            )
            
        except Exception as e:
            logger.error(f"Failed to create competition profile: {e}")
            raise
    
    @staticmethod
    async def update_profile(profile_id: str, updates: Dict) -> bool:
        """Update an existing competition profile"""
        try:
            result = await db.competition_profiles.update_one(
                {"_id": profile_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update competition profile {profile_id}: {e}")
            return False
    
    @staticmethod
    async def delete_profile(profile_id: str) -> bool:
        """Delete a competition profile"""
        try:
            # Check if any leagues are using this profile
            leagues_using_profile = await db.leagues.count_documents({
                "competition_profile": profile_id
            })
            
            if leagues_using_profile > 0:
                logger.warning(f"Cannot delete profile {profile_id}: {leagues_using_profile} leagues using it")
                return False
            
            result = await db.competition_profiles.delete_one({"_id": profile_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete competition profile {profile_id}: {e}")
            return False
    
    @staticmethod
    async def get_profiles_summary() -> Dict:
        """Get summary of all competition profiles"""
        try:
            profiles = await db.competition_profiles.find({}).to_list(length=None)
            
            summary = {
                "total_profiles": len(profiles),
                "profiles": []
            }
            
            for profile in profiles:
                # Count leagues using this profile
                league_count = await db.leagues.count_documents({
                    "competition_profile": profile["_id"]
                })
                
                summary["profiles"].append({
                    "id": profile["_id"],
                    "competition": profile["competition"],
                    "short_name": profile["short_name"],
                    "leagues_using": league_count,
                    "defaults": {
                        "budget": profile["defaults"]["budget_per_manager"],
                        "slots": profile["defaults"]["club_slots"],
                        "size": f"{profile['defaults']['league_size']['min']}-{profile['defaults']['league_size']['max']}"
                    }
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get profiles summary: {e}")
            return {"total_profiles": 0, "profiles": []}