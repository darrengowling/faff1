import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

from models import *
from database import db

logger = logging.getLogger(__name__)

class AggregationService:
    """
    Advanced MongoDB aggregation service for UCL Auction analytics
    Handles leaderboards, club management, and fixture analysis
    """
    
    @staticmethod
    async def get_league_leaderboard(league_id: str) -> Dict:
        """
        Get comprehensive league leaderboard with total points and weekly breakdown
        Uses the provided MongoDB aggregation pipeline
        """
        try:
            # Main leaderboard aggregation
            leaderboard_pipeline = [
                {"$match": {"league_id": league_id}},
                {"$group": {
                    "_id": {"user_id": "$user_id"},
                    "total": {"$sum": "$points_delta"},
                    "matches_played": {"$sum": 1},
                    "weekly_breakdown": {
                        "$push": {
                            "matchday": "$bucket.value",
                            "points": "$points_delta",
                            "match_id": "$match_id"
                        }
                    }
                }},
                {"$sort": {"total": -1}},
                {"$lookup": {
                    "from": "users",
                    "localField": "_id.user_id",
                    "foreignField": "_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$lookup": {
                    "from": "rosters",
                    "let": {"user_id": "$_id.user_id", "league_id": league_id},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$user_id", "$$user_id"]},
                                    {"$eq": ["$league_id", "$$league_id"]}
                                ]
                            }
                        }}
                    ],
                    "as": "roster"
                }},
                {"$unwind": "$roster"},
                {"$project": {
                    "user_id": "$_id.user_id",
                    "display_name": "$user.display_name",
                    "email": "$user.email",
                    "total_points": "$total",
                    "matches_played": "$matches_played",
                    "budget_remaining": "$roster.budget_remaining",
                    "budget_start": "$roster.budget_start",
                    "weekly_breakdown": "$weekly_breakdown",
                    "position": {"$literal": 0}  # Will be calculated after sorting
                }}
            ]
            
            leaderboard_results = await db.weekly_points.aggregate(leaderboard_pipeline).to_list(length=None)
            
            # Add position numbers
            for i, result in enumerate(leaderboard_results):
                result["position"] = i + 1
            
            # Get weekly/matchday breakdown aggregation
            weekly_breakdown = await AggregationService._get_weekly_breakdown(league_id)
            
            return {
                "league_id": league_id,
                "leaderboard": leaderboard_results,
                "weekly_breakdown": weekly_breakdown,
                "total_managers": len(leaderboard_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to get league leaderboard: {e}")
            return {
                "league_id": league_id,
                "leaderboard": [],
                "weekly_breakdown": {},
                "total_managers": 0
            }
    
    @staticmethod
    async def _get_weekly_breakdown(league_id: str) -> Dict:
        """
        Get weekly/matchday breakdown by $group on bucket.value
        """
        try:
            weekly_pipeline = [
                {"$match": {"league_id": league_id}},
                {"$group": {
                    "_id": {
                        "matchday": "$bucket.value",
                        "user_id": "$user_id"
                    },
                    "matchday_points": {"$sum": "$points_delta"},
                    "matches_in_matchday": {"$sum": 1}
                }},
                {"$group": {
                    "_id": "$_id.matchday",
                    "total_points_awarded": {"$sum": "$matchday_points"},
                    "total_matches": {"$sum": "$matches_in_matchday"},
                    "manager_performances": {
                        "$push": {
                            "user_id": "$_id.user_id",
                            "points": "$matchday_points",
                            "matches": "$matches_in_matchday"
                        }
                    }
                }},
                {"$sort": {"_id": 1}},  # Sort by matchday
                {"$lookup": {
                    "from": "users",
                    "localField": "manager_performances.user_id",
                    "foreignField": "_id",
                    "as": "user_details"
                }}
            ]
            
            weekly_results = await db.weekly_points.aggregate(weekly_pipeline).to_list(length=None)
            
            # Transform results into a more usable format
            breakdown = {}
            for week in weekly_results:
                matchday = week["_id"]
                breakdown[f"matchday_{matchday}"] = {
                    "matchday": matchday,
                    "total_points": week["total_points_awarded"],
                    "total_matches": week["total_matches"],
                    "top_performers": sorted(
                        week["manager_performances"], 
                        key=lambda x: x["points"], 
                        reverse=True
                    )[:3]  # Top 3 performers for this matchday
                }
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to get weekly breakdown: {e}")
            return {}
    
    @staticmethod
    async def get_user_clubs(league_id: str, user_id: str) -> Dict:
        """
        Get user's owned clubs with prices, budget info, and upcoming fixtures
        """
        try:
            # Get user's clubs with details
            clubs_pipeline = [
                {"$match": {"league_id": league_id, "user_id": user_id}},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "club_id",
                    "foreignField": "_id",
                    "as": "club"
                }},
                {"$unwind": "$club"},
                {"$lookup": {
                    "from": "rosters",
                    "let": {"user_id": user_id, "league_id": league_id},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$user_id", "$$user_id"]},
                                    {"$eq": ["$league_id", "$$league_id"]}
                                ]
                            }
                        }}
                    ],
                    "as": "roster"
                }},
                {"$unwind": "$roster"},
                {"$project": {
                    "club_id": "$club_id",
                    "club_name": "$club.name",
                    "club_short_name": "$club.short_name",
                    "club_country": "$club.country",
                    "club_ext_ref": "$club.ext_ref",
                    "price_paid": "$price",
                    "acquired_at": "$acquired_at",
                    "budget_remaining": "$roster.budget_remaining",
                    "budget_start": "$roster.budget_start",
                    "club_slots": "$roster.club_slots"
                }},
                {"$sort": {"acquired_at": -1}}
            ]
            
            owned_clubs = await db.roster_clubs.aggregate(clubs_pipeline).to_list(length=None)
            
            # Get upcoming fixtures for owned clubs
            club_ext_refs = [club["club_ext_ref"] for club in owned_clubs]
            upcoming_fixtures = await AggregationService._get_upcoming_fixtures(league_id, club_ext_refs)
            
            # Get recent results and points for owned clubs
            recent_results = await AggregationService._get_recent_results(league_id, user_id)
            
            # Calculate summary statistics
            total_spent = sum(club["price_paid"] for club in owned_clubs)
            budget_info = {
                "budget_start": owned_clubs[0]["budget_start"] if owned_clubs else 100,
                "budget_remaining": owned_clubs[0]["budget_remaining"] if owned_clubs else 100,
                "total_spent": total_spent,
                "clubs_owned": len(owned_clubs),
                "slots_available": owned_clubs[0]["club_slots"] - len(owned_clubs) if owned_clubs else 3
            }
            
            return {
                "league_id": league_id,
                "user_id": user_id,
                "owned_clubs": owned_clubs,
                "upcoming_fixtures": upcoming_fixtures,
                "recent_results": recent_results,
                "budget_info": budget_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get user clubs: {e}")
            return {
                "league_id": league_id,
                "user_id": user_id,
                "owned_clubs": [],
                "upcoming_fixtures": [],
                "recent_results": [],
                "budget_info": {}
            }
    
    @staticmethod
    async def _get_upcoming_fixtures(league_id: str, club_ext_refs: List[str]) -> List[Dict]:
        """
        Get upcoming fixtures for specified clubs
        """
        try:
            now = datetime.now(timezone.utc)
            
            upcoming_pipeline = [
                {"$match": {
                    "league_id": league_id,
                    "date": {"$gte": now},
                    "$or": [
                        {"home_ext": {"$in": club_ext_refs}},
                        {"away_ext": {"$in": club_ext_refs}}
                    ]
                }},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "home_ext",
                    "foreignField": "ext_ref",
                    "as": "home_club"
                }},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "away_ext",
                    "foreignField": "ext_ref",
                    "as": "away_club"
                }},
                {"$project": {
                    "match_id": 1,
                    "date": 1,
                    "status": 1,
                    "home_ext": 1,
                    "away_ext": 1,
                    "home_club": {"$arrayElemAt": ["$home_club", 0]},
                    "away_club": {"$arrayElemAt": ["$away_club", 0]},
                    "is_home": {"$in": ["$home_ext", club_ext_refs]},
                    "is_away": {"$in": ["$away_ext", club_ext_refs]}
                }},
                {"$sort": {"date": 1}},
                {"$limit": 10}  # Next 10 fixtures
            ]
            
            return await db.fixtures.aggregate(upcoming_pipeline).to_list(length=None)
            
        except Exception as e:
            logger.error(f"Failed to get upcoming fixtures: {e}")
            return []
    
    @staticmethod
    async def _get_recent_results(league_id: str, user_id: str) -> List[Dict]:
        """
        Get recent match results and points for a user
        """
        try:
            recent_pipeline = [
                {"$match": {"league_id": league_id, "user_id": user_id}},
                {"$lookup": {
                    "from": "result_ingest",
                    "localField": "match_id",
                    "foreignField": "match_id",
                    "as": "match"
                }},
                {"$unwind": "$match"},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "match.home_ext",
                    "foreignField": "ext_ref",
                    "as": "home_club"
                }},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "match.away_ext",
                    "foreignField": "ext_ref",
                    "as": "away_club"
                }},
                {"$project": {
                    "match_id": 1,
                    "points_delta": 1,
                    "bucket": 1,
                    "created_at": 1,
                    "match_date": "$match.kicked_off_at",
                    "home_ext": "$match.home_ext",
                    "away_ext": "$match.away_ext",
                    "home_goals": "$match.home_goals",
                    "away_goals": "$match.away_goals",
                    "home_club": {"$arrayElemAt": ["$home_club", 0]},
                    "away_club": {"$arrayElemAt": ["$away_club", 0]}
                }},
                {"$sort": {"match_date": -1}},
                {"$limit": 5}  # Last 5 results
            ]
            
            return await db.weekly_points.aggregate(recent_pipeline).to_list(length=None)
            
        except Exception as e:
            logger.error(f"Failed to get recent results: {e}")
            return []
    
    @staticmethod
    async def get_league_fixtures(league_id: str, season: str = "2024-25") -> Dict:
        """
        Get all UCL fixtures for the season with ownership badges
        """
        try:
            # Get all fixtures for the league/season
            fixtures_pipeline = [
                {"$match": {"league_id": league_id, "season": season}},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "home_ext",
                    "foreignField": "ext_ref",
                    "as": "home_club"
                }},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "away_ext",
                    "foreignField": "ext_ref",
                    "as": "away_club"
                }},
                {"$project": {
                    "match_id": 1,
                    "date": 1,
                    "status": 1,
                    "home_ext": 1,
                    "away_ext": 1,
                    "home_club": {"$arrayElemAt": ["$home_club", 0]},
                    "away_club": {"$arrayElemAt": ["$away_club", 0]}
                }},
                {"$sort": {"date": 1}}
            ]
            
            fixtures = await db.fixtures.aggregate(fixtures_pipeline).to_list(length=None)
            
            # Get club ownership information for the league
            ownership_pipeline = [
                {"$match": {"league_id": league_id}},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "club_id",
                    "foreignField": "_id",
                    "as": "club"
                }},
                {"$unwind": "$club"},
                {"$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$group": {
                    "_id": "$club.ext_ref",
                    "club_name": {"$first": "$club.name"},
                    "club_short_name": {"$first": "$club.short_name"},
                    "owners": {
                        "$push": {
                            "user_id": "$user_id",
                            "display_name": "$user.display_name",
                            "price": "$price"
                        }
                    }
                }}
            ]
            
            ownership_data = await db.roster_clubs.aggregate(ownership_pipeline).to_list(length=None)
            ownership_map = {item["_id"]: item for item in ownership_data}
            
            # Get match results for completed fixtures
            results_pipeline = [
                {"$match": {"league_id": league_id}},
                {"$project": {
                    "match_id": 1,
                    "home_ext": 1,
                    "away_ext": 1,
                    "home_goals": 1,
                    "away_goals": 1,
                    "status": 1
                }}
            ]
            
            results = await db.result_ingest.aggregate(results_pipeline).to_list(length=None)
            results_map = {result["match_id"]: result for result in results}
            
            # Combine fixtures with ownership and results
            enhanced_fixtures = []
            for fixture in fixtures:
                enhanced_fixture = fixture.copy()
                
                # Add ownership badges
                enhanced_fixture["home_owners"] = ownership_map.get(fixture["home_ext"], {}).get("owners", [])
                enhanced_fixture["away_owners"] = ownership_map.get(fixture["away_ext"], {}).get("owners", [])
                
                # Add results if available
                if fixture["match_id"] in results_map:
                    result = results_map[fixture["match_id"]]
                    enhanced_fixture["home_goals"] = result["home_goals"]
                    enhanced_fixture["away_goals"] = result["away_goals"]
                    enhanced_fixture["result_status"] = result["status"]
                
                enhanced_fixtures.append(enhanced_fixture)
            
            # Group fixtures by matchday/competition stage
            grouped_fixtures = AggregationService._group_fixtures_by_stage(enhanced_fixtures)
            
            return {
                "league_id": league_id,
                "season": season,
                "fixtures": enhanced_fixtures,
                "grouped_fixtures": grouped_fixtures,
                "ownership_summary": ownership_map
            }
            
        except Exception as e:
            logger.error(f"Failed to get league fixtures: {e}")
            return {
                "league_id": league_id,
                "season": season,
                "fixtures": [],
                "grouped_fixtures": {},
                "ownership_summary": {}
            }
    
    @staticmethod
    def _group_fixtures_by_stage(fixtures: List[Dict]) -> Dict:
        """
        Group fixtures by competition stage (Group Stage, Knockout, etc.)
        """
        try:
            grouped = {
                "group_stage": [],
                "round_of_16": [],
                "quarter_finals": [],
                "semi_finals": [],
                "final": []
            }
            
            now = datetime.now(timezone.utc)
            season_start = datetime(2024, 9, 1, tzinfo=timezone.utc)
            
            for fixture in fixtures:
                fixture_date = fixture["date"]
                if isinstance(fixture_date, str):
                    fixture_date = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
                
                days_since_start = (fixture_date - season_start).days
                
                if days_since_start < 84:  # Group stage
                    grouped["group_stage"].append(fixture)
                elif days_since_start < 114:  # Round of 16
                    grouped["round_of_16"].append(fixture)
                elif days_since_start < 144:  # Quarter-finals
                    grouped["quarter_finals"].append(fixture)
                elif days_since_start < 174:  # Semi-finals
                    grouped["semi_finals"].append(fixture)
                else:  # Final
                    grouped["final"].append(fixture)
            
            return grouped
            
        except Exception as e:
            logger.error(f"Failed to group fixtures: {e}")
            return {}
    
    @staticmethod
    async def get_manager_head_to_head(league_id: str, user1_id: str, user2_id: str) -> Dict:
        """
        Get head-to-head comparison between two managers
        """
        try:
            comparison_pipeline = [
                {"$match": {
                    "league_id": league_id,
                    "user_id": {"$in": [user1_id, user2_id]}
                }},
                {"$group": {
                    "_id": "$user_id",
                    "total_points": {"$sum": "$points_delta"},
                    "matches_played": {"$sum": 1},
                    "best_matchday": {"$max": "$points_delta"},
                    "worst_matchday": {"$min": "$points_delta"},
                    "avg_points": {"$avg": "$points_delta"}
                }},
                {"$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$project": {
                    "user_id": "$_id",
                    "display_name": "$user.display_name",
                    "total_points": 1,
                    "matches_played": 1,
                    "best_matchday": 1,
                    "worst_matchday": 1,
                    "avg_points": {"$round": ["$avg_points", 2]}
                }}
            ]
            
            comparison_results = await db.weekly_points.aggregate(comparison_pipeline).to_list(length=None)
            
            return {
                "league_id": league_id,
                "comparison": comparison_results
            }
            
        except Exception as e:
            logger.error(f"Failed to get head-to-head comparison: {e}")
            return {"league_id": league_id, "comparison": []}

# Convenience functions for easy access
async def get_leaderboard(league_id: str) -> Dict:
    """Get league leaderboard"""
    return await AggregationService.get_league_leaderboard(league_id)

async def get_my_clubs(league_id: str, user_id: str) -> Dict:
    """Get user's clubs"""
    return await AggregationService.get_user_clubs(league_id, user_id)

async def get_fixtures(league_id: str, season: str = "2024-25") -> Dict:
    """Get league fixtures"""
    return await AggregationService.get_league_fixtures(league_id, season)