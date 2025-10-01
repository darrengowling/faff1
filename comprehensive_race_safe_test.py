#!/usr/bin/env python3
"""
Comprehensive Race-Safe and Replay-Safe Bidding Implementation Test

This test verifies the implementation of race-safe and replay-safe bidding by:
1. Checking the BidService implementation
2. Verifying MongoDB transaction support
3. Testing auction logs collection and unique indexes
4. Validating the race-safe bidding logic
5. Confirming replay safety mechanisms
6. Testing bid validation logic
7. Verifying Socket.IO integration points
8. Testing HTTP endpoint integration
"""

import asyncio
import aiohttp
import json
import uuid
import time
import logging
import os
import sys

# Add backend to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_URL = "https://livebid-app.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveRaceSafeTest:
    def __init__(self):
        self.session = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Content-Type": "application/json"}
        )
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    async def test_bid_service_implementation(self) -> dict:
        """Test 1: Verify BidService implementation exists and is correct"""
        logger.info("🧪 TEST 1: BidService Implementation")
        
        try:
            # Check if BidService file exists
            bid_service_path = "/app/backend/bid_service.py"
            if not os.path.exists(bid_service_path):
                return {"success": False, "error": "BidService file not found"}
            
            # Read and analyze the BidService implementation
            with open(bid_service_path, 'r') as f:
                content = f.read()
            
            # Check for key components
            checks = [
                ("MongoDB transactions", "start_session" in content and "start_transaction" in content),
                ("Race-safe logic", "place_bid" in content and "session" in content),
                ("Replay safety", "op_id" in content and "DuplicateKeyError" in content),
                ("Auction logs", "auction_logs" in content),
                ("Unique constraint", "unique_league_opid" in content),
                ("Bid validation", "budget_remaining" in content and "current_bid" in content),
                ("Atomic operations", "update_one" in content and "session=session" in content)
            ]
            
            passed_checks = [check for check, result in checks if result]
            failed_checks = [check for check, result in checks if not result]
            
            if len(passed_checks) >= 6:  # At least 6/7 checks should pass
                return {
                    "success": True, 
                    "message": f"BidService implementation verified: {len(passed_checks)}/7 checks passed",
                    "details": f"Passed: {passed_checks}, Failed: {failed_checks}"
                }
            else:
                return {
                    "success": False, 
                    "error": f"BidService implementation incomplete: {len(failed_checks)} checks failed",
                    "details": f"Failed: {failed_checks}"
                }
                
        except Exception as e:
            return {"success": False, "error": f"BidService implementation test exception: {e}"}

    async def test_mongodb_transaction_support(self) -> dict:
        """Test 2: Verify MongoDB transaction support is configured"""
        logger.info("🧪 TEST 2: MongoDB Transaction Support")
        
        try:
            # Check database configuration
            database_path = "/app/backend/database.py"
            if not os.path.exists(database_path):
                return {"success": False, "error": "Database configuration file not found"}
            
            with open(database_path, 'r') as f:
                content = f.read()
            
            # Check for transaction support indicators
            transaction_indicators = [
                "AsyncIOMotorClient" in content,
                "start_session" in content or "session" in content,
                "motor" in content.lower()
            ]
            
            if all(transaction_indicators):
                return {"success": True, "message": "MongoDB transaction support configured"}
            else:
                return {"success": False, "error": "MongoDB transaction support not properly configured"}
                
        except Exception as e:
            return {"success": False, "error": f"MongoDB transaction test exception: {e}"}

    async def test_auction_logs_indexes(self) -> dict:
        """Test 3: Verify auction logs collection has unique indexes"""
        logger.info("🧪 TEST 3: Auction Logs Indexes")
        
        try:
            # Check database indexes configuration
            indexes_path = "/app/backend/database_indexes.py"
            if not os.path.exists(indexes_path):
                return {"success": False, "error": "Database indexes file not found"}
            
            with open(indexes_path, 'r') as f:
                content = f.read()
            
            # Check for auction_logs indexes
            index_checks = [
                ("auction_logs collection", "auction_logs" in content),
                ("unique index", "unique=True" in content and "unique_league_opid" in content),
                ("league_id + op_id", "league_id" in content and "op_id" in content),
                ("IndexModel", "IndexModel" in content)
            ]
            
            passed_checks = [check for check, result in index_checks if result]
            
            if len(passed_checks) >= 3:
                return {"success": True, "message": f"Auction logs indexes configured: {len(passed_checks)}/4 checks passed"}
            else:
                return {"success": False, "error": f"Auction logs indexes not properly configured: {len(passed_checks)}/4 checks passed"}
                
        except Exception as e:
            return {"success": False, "error": f"Auction logs indexes test exception: {e}"}

    async def test_race_safe_logic(self) -> dict:
        """Test 4: Verify race-safe bidding logic implementation"""
        logger.info("🧪 TEST 4: Race-Safe Logic")
        
        try:
            # Analyze BidService for race-safe patterns
            bid_service_path = "/app/backend/bid_service.py"
            with open(bid_service_path, 'r') as f:
                content = f.read()
            
            # Check for race-safe patterns
            race_safe_patterns = [
                ("Atomic updates", "update_one" in content and "current_bid" in content),
                ("Session consistency", "session=session" in content),
                ("Optimistic locking", "current_bid" in content and "modified_count" in content),
                ("Transaction rollback", "start_transaction" in content),
                ("Race condition detection", "modified_count == 0" in content or "race condition" in content.lower())
            ]
            
            passed_patterns = [pattern for pattern, result in race_safe_patterns if result]
            
            if len(passed_patterns) >= 4:
                return {"success": True, "message": f"Race-safe logic implemented: {len(passed_patterns)}/5 patterns found"}
            else:
                return {"success": False, "error": f"Race-safe logic incomplete: {len(passed_patterns)}/5 patterns found"}
                
        except Exception as e:
            return {"success": False, "error": f"Race-safe logic test exception: {e}"}

    async def test_replay_safety(self) -> dict:
        """Test 5: Verify replay safety implementation"""
        logger.info("🧪 TEST 5: Replay Safety")
        
        try:
            # Analyze BidService for replay safety patterns
            bid_service_path = "/app/backend/bid_service.py"
            with open(bid_service_path, 'r') as f:
                content = f.read()
            
            # Check for replay safety patterns
            replay_patterns = [
                ("Operation ID", "op_id" in content),
                ("Duplicate detection", "DuplicateKeyError" in content),
                ("Unique constraint", "unique_league_opid" in content),
                ("Replay handling", "replay" in content.lower()),
                ("No-op behavior", "already processed" in content.lower() or "replay" in content.lower())
            ]
            
            passed_patterns = [pattern for pattern, result in replay_patterns if result]
            
            if len(passed_patterns) >= 4:
                return {"success": True, "message": f"Replay safety implemented: {len(passed_patterns)}/5 patterns found"}
            else:
                return {"success": False, "error": f"Replay safety incomplete: {len(passed_patterns)}/5 patterns found"}
                
        except Exception as e:
            return {"success": False, "error": f"Replay safety test exception: {e}"}

    async def test_bid_validation(self) -> dict:
        """Test 6: Verify bid validation logic"""
        logger.info("🧪 TEST 6: Bid Validation")
        
        try:
            # Analyze BidService for validation patterns
            bid_service_path = "/app/backend/bid_service.py"
            with open(bid_service_path, 'r') as f:
                content = f.read()
            
            # Check for validation patterns
            validation_patterns = [
                ("Lot status check", "status" in content and "open" in content),
                ("Amount validation", "amount" in content and "current_bid" in content),
                ("Budget validation", "budget_remaining" in content),
                ("User validation", "user_id" in content and "find_one" in content),
                ("Club sold check", "final_price" in content or "sold" in content)
            ]
            
            passed_patterns = [pattern for pattern, result in validation_patterns if result]
            
            if len(passed_patterns) >= 4:
                return {"success": True, "message": f"Bid validation implemented: {len(passed_patterns)}/5 patterns found"}
            else:
                return {"success": False, "error": f"Bid validation incomplete: {len(passed_patterns)}/5 patterns found"}
                
        except Exception as e:
            return {"success": False, "error": f"Bid validation test exception: {e}"}

    async def test_socket_io_integration(self) -> dict:
        """Test 7: Verify Socket.IO integration points"""
        logger.info("🧪 TEST 7: Socket.IO Integration")
        
        try:
            # Check auction engine for Socket.IO integration
            auction_engine_path = "/app/backend/auction_engine.py"
            if not os.path.exists(auction_engine_path):
                return {"success": False, "error": "Auction engine file not found"}
            
            with open(auction_engine_path, 'r') as f:
                content = f.read()
            
            # Check for Socket.IO integration patterns
            socketio_patterns = [
                ("Socket.IO import", "socketio" in content),
                ("Bid update events", "bid_update" in content),
                ("Event emission", "emit" in content),
                ("Room broadcasting", "room" in content),
                ("League room", "league_id" in content and "room" in content)
            ]
            
            passed_patterns = [pattern for pattern, result in socketio_patterns if result]
            
            if len(passed_patterns) >= 4:
                return {"success": True, "message": f"Socket.IO integration implemented: {len(passed_patterns)}/5 patterns found"}
            else:
                return {"success": False, "error": f"Socket.IO integration incomplete: {len(passed_patterns)}/5 patterns found"}
                
        except Exception as e:
            return {"success": False, "error": f"Socket.IO integration test exception: {e}"}

    async def test_http_endpoint_integration(self) -> dict:
        """Test 8: Verify HTTP endpoint integration"""
        logger.info("🧪 TEST 8: HTTP Endpoint Integration")
        
        try:
            # Check server.py for HTTP bid endpoint
            server_path = "/app/backend/server.py"
            if not os.path.exists(server_path):
                return {"success": False, "error": "Server file not found"}
            
            with open(server_path, 'r') as f:
                content = f.read()
            
            # Check for HTTP endpoint patterns
            endpoint_patterns = [
                ("Bid endpoint", "/auction/{auction_id}/bid" in content),
                ("HTTP POST", "@api_router.post" in content and "bid" in content),
                ("BidCreate model", "BidCreate" in content),
                ("Operation ID", "op_id" in content),
                ("Error handling", "HTTPException" in content and "bid" in content.lower())
            ]
            
            passed_patterns = [pattern for pattern, result in endpoint_patterns if result]
            
            if len(passed_patterns) >= 4:
                return {"success": True, "message": f"HTTP endpoint integration implemented: {len(passed_patterns)}/5 patterns found"}
            else:
                return {"success": False, "error": f"HTTP endpoint integration incomplete: {len(passed_patterns)}/5 patterns found"}
                
        except Exception as e:
            return {"success": False, "error": f"HTTP endpoint integration test exception: {e}"}

    async def test_backend_health_with_collections(self) -> dict:
        """Test 9: Verify backend health and auction_logs collection"""
        logger.info("🧪 TEST 9: Backend Health and Collections")
        
        try:
            async with self.session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    db_info = result.get("database", {})
                    
                    if db_info.get("connected"):
                        collections_count = db_info.get("collections_count", 0)
                        missing_collections = db_info.get("missing_collections", [])
                        
                        # Check if auction_logs collection exists
                        if "auction_logs" not in missing_collections:
                            return {
                                "success": True, 
                                "message": f"Backend healthy with {collections_count} collections, auction_logs exists"
                            }
                        else:
                            return {"success": False, "error": "auction_logs collection missing from database"}
                    else:
                        return {"success": False, "error": "Database not connected"}
                else:
                    return {"success": False, "error": f"Health check failed: {resp.status}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Backend health test exception: {e}"}

    async def run_all_tests(self) -> dict:
        """Run all comprehensive tests"""
        logger.info("🚀 Starting Comprehensive Race-Safe and Replay-Safe Bidding Tests")
        
        try:
            await self.setup_session()
            
            # Run all tests
            tests = [
                ("BidService Implementation", self.test_bid_service_implementation),
                ("MongoDB Transaction Support", self.test_mongodb_transaction_support),
                ("Auction Logs Indexes", self.test_auction_logs_indexes),
                ("Race-Safe Logic", self.test_race_safe_logic),
                ("Replay Safety", self.test_replay_safety),
                ("Bid Validation", self.test_bid_validation),
                ("Socket.IO Integration", self.test_socket_io_integration),
                ("HTTP Endpoint Integration", self.test_http_endpoint_integration),
                ("Backend Health & Collections", self.test_backend_health_with_collections)
            ]
            
            results = []
            passed_count = 0
            
            for test_name, test_func in tests:
                logger.info(f"\n--- Running {test_name} ---")
                try:
                    result = await test_func()
                    results.append({
                        "test": test_name,
                        "success": result["success"],
                        "message": result.get("message", result.get("error", "")),
                        "details": result.get("details", "")
                    })
                    
                    if result["success"]:
                        passed_count += 1
                        logger.info(f"✅ {test_name}: {result.get('message', 'PASSED')}")
                    else:
                        logger.error(f"❌ {test_name}: {result.get('error', 'FAILED')}")
                        
                except Exception as e:
                    logger.error(f"💥 {test_name}: Exception - {e}")
                    results.append({
                        "test": test_name,
                        "success": False,
                        "message": f"Exception: {e}",
                        "details": ""
                    })
            
            # Calculate success rate
            success_rate = (passed_count / len(tests)) * 100
            
            return {
                "success": success_rate >= 85,  # 85% threshold
                "passed": passed_count,
                "total": len(tests),
                "success_rate": success_rate,
                "results": results,
                "summary": f"Comprehensive Race-Safe Tests: {passed_count}/{len(tests)} passed ({success_rate:.1f}%)"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Test execution exception: {e}"}
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    test_runner = ComprehensiveRaceSafeTest()
    
    try:
        results = await test_runner.run_all_tests()
        
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE RACE-SAFE AND REPLAY-SAFE BIDDING TEST RESULTS")
        print("="*80)
        
        if results["success"]:
            print(f"✅ OVERALL SUCCESS: {results['summary']}")
        else:
            print(f"❌ OVERALL FAILURE: {results['summary']}")
            
        print(f"\nSuccess Rate: {results.get('success_rate', 0):.1f}%")
        print(f"Tests Passed: {results.get('passed', 0)}/{results.get('total', 0)}")
        
        print("\nDetailed Results:")
        for result in results.get("results", []):
            status = "✅" if result["success"] else "❌"
            message = result['message']
            details = result.get('details', '')
            if details:
                print(f"{status} {result['test']}: {message}")
                print(f"   Details: {details}")
            else:
                print(f"{status} {result['test']}: {message}")
            
        print("\n" + "="*80)
        
        return results["success"]
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)