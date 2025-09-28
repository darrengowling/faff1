from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'ucl_auction')

client = AsyncIOMotorClient(MONGO_URL)
db: AsyncIOMotorDatabase = client[DB_NAME]

# JSON Schema validators for collections
SCHEMAS = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "email", "display_name", "created_at", "verified"],
            "properties": {
                "_id": {"bsonType": "string"},
                "email": {"bsonType": "string", "pattern": "^(?P<local>[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*)@(?P<domain>(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)$"},
                "display_name": {"bsonType": "string", "minLength": 1, "maxLength": 100},
                "created_at": {"bsonType": "date"},
                "verified": {"bsonType": "bool"}
            }
        }
    },
    "leagues": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "name", "competition", "season", "commissioner_id", "settings", "status", "member_count", "created_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "name": {"bsonType": "string", "minLength": 1, "maxLength": 100},
                "competition": {"bsonType": "string", "enum": ["UCL"]},
                "season": {"bsonType": "string"},
                "commissioner_id": {"bsonType": "string"},
                "status": {"bsonType": "string", "enum": ["setup", "ready", "active", "completed"]},
                "member_count": {"bsonType": "int", "minimum": 1, "maximum": 8},
                "settings": {
                    "bsonType": "object",
                    "properties": {
                        "budget_per_manager": {"bsonType": "int", "minimum": 1},
                        "min_increment": {"bsonType": "int", "minimum": 1},
                        "club_slots_per_manager": {"bsonType": "int", "minimum": 1},
                        "anti_snipe_seconds": {"bsonType": "int", "minimum": 0},
                        "bid_timer_seconds": {"bsonType": "int", "minimum": 1},
                        "max_managers": {"bsonType": "int", "minimum": 4, "maximum": 8},
                        "min_managers": {"bsonType": "int", "minimum": 4, "maximum": 8},
                        "scoring_rules": {
                            "bsonType": "object",
                            "properties": {
                                "club_goal": {"bsonType": "int"},
                                "club_win": {"bsonType": "int"},
                                "club_draw": {"bsonType": "int"}
                            }
                        }
                    }
                },
                "created_at": {"bsonType": "date"}
            }
        }
    },
    "memberships": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "user_id", "role", "status", "joined_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "role": {"bsonType": "string", "enum": ["commissioner", "manager"]},
                "status": {"bsonType": "string", "enum": ["active", "pending"]},
                "joined_at": {"bsonType": "date"}
            }
        }
    },
    "invitations": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "inviter_id", "email", "token", "status", "expires_at", "created_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "inviter_id": {"bsonType": "string"},
                "email": {"bsonType": "string", "pattern": "^(?P<local>[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*)@(?P<domain>(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)$"},
                "token": {"bsonType": "string"},
                "status": {"bsonType": "string", "enum": ["pending", "accepted", "expired"]},
                "expires_at": {"bsonType": "date"},
                "created_at": {"bsonType": "date"},
                "accepted_at": {"bsonType": ["date", "null"]}
            }
        }
    },
    "clubs": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "name", "short_name", "country", "ext_ref"],
            "properties": {
                "_id": {"bsonType": "string"},
                "name": {"bsonType": "string", "minLength": 1},
                "short_name": {"bsonType": "string", "minLength": 1},
                "country": {"bsonType": "string", "minLength": 1},
                "ext_ref": {"bsonType": "string", "minLength": 1}
            }
        }
    },
    "auctions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "status", "nomination_order", "budget_per_manager", "min_increment", "anti_snipe_seconds", "bid_timer_seconds", "created_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "status": {"bsonType": "string", "enum": ["scheduled", "live", "paused", "completed"]},
                "nomination_order": {"bsonType": "array", "items": {"bsonType": "string"}},
                "budget_per_manager": {"bsonType": "int", "minimum": 1},
                "min_increment": {"bsonType": "int", "minimum": 1},
                "anti_snipe_seconds": {"bsonType": "int", "minimum": 0},
                "bid_timer_seconds": {"bsonType": "int", "minimum": 1},
                "created_at": {"bsonType": "date"}
            }
        }
    },
    "lots": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "auction_id", "club_id", "status", "order_index", "current_bid", "created_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "auction_id": {"bsonType": "string"},
                "club_id": {"bsonType": "string"},
                "status": {"bsonType": "string", "enum": ["pending", "open", "sold", "unsold"]},
                "nominated_by": {"bsonType": ["string", "null"]},
                "order_index": {"bsonType": "int", "minimum": 0},
                "current_bid": {"bsonType": "int", "minimum": 0},
                "top_bidder_id": {"bsonType": ["string", "null"]},
                "timer_ends_at": {"bsonType": ["date", "null"]},
                "created_at": {"bsonType": "date"}
            }
        }
    },
    "bids": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "lot_id", "bidder_id", "amount", "created_at", "server_ts"],
            "properties": {
                "_id": {"bsonType": "string"},
                "lot_id": {"bsonType": "string"},
                "bidder_id": {"bsonType": "string"},
                "amount": {"bsonType": "int", "minimum": 1},
                "created_at": {"bsonType": "date"},
                "server_ts": {"bsonType": "date"}
            }
        }
    },
    "rosters": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "user_id", "budget_start", "budget_remaining", "club_slots"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "budget_start": {"bsonType": "int", "minimum": 0},
                "budget_remaining": {"bsonType": "int", "minimum": 0},
                "club_slots": {"bsonType": "int", "minimum": 1}
            }
        }
    },
    "roster_clubs": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "roster_id", "league_id", "user_id", "club_id", "price", "acquired_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "roster_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "club_id": {"bsonType": "string"},
                "price": {"bsonType": "int", "minimum": 1},
                "acquired_at": {"bsonType": "date"}
            }
        }
    },
    "scoring_rules": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "rules"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "rules": {
                    "bsonType": "object",
                    "properties": {
                        "club_goal": {"bsonType": "int"},
                        "club_win": {"bsonType": "int"},
                        "club_draw": {"bsonType": "int"}
                    }
                }
            }
        }
    },
    "fixtures": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "season", "match_id", "date", "home_ext", "away_ext", "status"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "season": {"bsonType": "string"},
                "match_id": {"bsonType": "string"},
                "date": {"bsonType": "date"},
                "home_ext": {"bsonType": "string"},
                "away_ext": {"bsonType": "string"},
                "status": {"bsonType": "string"}
            }
        }
    },
    "result_ingest": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "match_id", "home_ext", "away_ext", "home_goals", "away_goals", "kicked_off_at", "status", "received_at", "processed"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "match_id": {"bsonType": "string"},
                "home_ext": {"bsonType": "string"},
                "away_ext": {"bsonType": "string"},
                "home_goals": {"bsonType": "int", "minimum": 0},
                "away_goals": {"bsonType": "int", "minimum": 0},
                "kicked_off_at": {"bsonType": "date"},
                "status": {"bsonType": "string"},
                "received_at": {"bsonType": "date"},
                "processed": {"bsonType": "bool"}
            }
        }
    },
    "settlements": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "match_id", "processed_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "match_id": {"bsonType": "string"},
                "processed_at": {"bsonType": "date"}
            }
        }
    },
    "weekly_points": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "league_id", "user_id", "bucket", "points_delta", "match_id", "created_at"],
            "properties": {
                "_id": {"bsonType": "string"},
                "league_id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "bucket": {
                    "bsonType": "object",
                    "properties": {
                        "type": {"bsonType": "string"},
                        "value": {"bsonType": "int"}
                    }
                },
                "points_delta": {"bsonType": "int"},
                "match_id": {"bsonType": "string"},
                "created_at": {"bsonType": "date"}
            }
        }
    }
}

# Index definitions
INDEXES = {
    "users": [
        IndexModel([("email", ASCENDING)], unique=True)
    ],
    "leagues": [
        IndexModel([("commissioner_id", ASCENDING)]),
        IndexModel([("competition", ASCENDING), ("season", ASCENDING)]),
        IndexModel([("status", ASCENDING)])
    ],
    "memberships": [
        IndexModel([("league_id", ASCENDING), ("user_id", ASCENDING)], unique=True),
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("league_id", ASCENDING), ("status", ASCENDING)])
    ],
    "invitations": [
        IndexModel([("league_id", ASCENDING), ("email", ASCENDING)]),
        IndexModel([("token", ASCENDING)], unique=True),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("expires_at", ASCENDING)])
    ],
    "clubs": [
        IndexModel([("ext_ref", ASCENDING)], unique=True),
        IndexModel([("name", ASCENDING)])
    ],
    "auctions": [
        IndexModel([("league_id", ASCENDING)]),
        IndexModel([("status", ASCENDING)])
    ],
    "lots": [
        IndexModel([("auction_id", ASCENDING), ("club_id", ASCENDING)], unique=True),
        IndexModel([("auction_id", ASCENDING), ("order_index", ASCENDING)]),
        IndexModel([("status", ASCENDING)])
    ],
    "bids": [
        IndexModel([("lot_id", ASCENDING), ("created_at", ASCENDING)]),
        IndexModel([("bidder_id", ASCENDING)]),
        IndexModel([("server_ts", ASCENDING)])
    ],
    "rosters": [
        IndexModel([("league_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    ],
    "roster_clubs": [
        IndexModel([("league_id", ASCENDING), ("club_id", ASCENDING)], unique=True),
        IndexModel([("roster_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING)])
    ],
    "scoring_rules": [
        IndexModel([("league_id", ASCENDING)], unique=True)
    ],
    "fixtures": [
        IndexModel([("league_id", ASCENDING), ("match_id", ASCENDING)], unique=True),
        IndexModel([("season", ASCENDING)]),
        IndexModel([("date", ASCENDING)])
    ],
    "result_ingest": [
        IndexModel([("processed", ASCENDING)]),
        IndexModel([("league_id", ASCENDING), ("match_id", ASCENDING)]),
        IndexModel([("received_at", ASCENDING)])
    ],
    "settlements": [
        IndexModel([("league_id", ASCENDING), ("match_id", ASCENDING)], unique=True)
    ],
    "weekly_points": [
        IndexModel([("league_id", ASCENDING), ("user_id", ASCENDING), ("match_id", ASCENDING)], unique=True),
        IndexModel([("league_id", ASCENDING), ("bucket.type", ASCENDING), ("bucket.value", ASCENDING)])
    ]
}

async def initialize_database():
    """Initialize database with schemas and indexes"""
    try:
        # Get list of existing collections
        existing_collections = await db.list_collection_names()
        
        for collection_name, schema in SCHEMAS.items():
            if collection_name not in existing_collections:
                # Create collection with schema validation
                await db.create_collection(
                    collection_name,
                    validator=schema
                )
                logger.info(f"Created collection '{collection_name}' with schema validation")
            else:
                # Update existing collection with schema validation
                await db.command({
                    "collMod": collection_name,
                    "validator": schema
                })
                logger.info(f"Updated schema validation for collection '{collection_name}'")
            
            # Create indexes for the collection
            if collection_name in INDEXES:
                collection = db[collection_name]
                await collection.create_indexes(INDEXES[collection_name])
                logger.info(f"Created indexes for collection '{collection_name}'")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def get_database():
    """Get database instance"""
    return db

async def close_database():
    """Close database connection"""
    client.close()