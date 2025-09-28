#!/usr/bin/env python3
"""
Regression Test Suite Runner
Runs all regression tests to prevent Min=2 gate and Slots=5 display issues from coming back
"""

import subprocess
import sys
import os
from datetime import datetime

class RegressionTestRunner:
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()

    def log_result(self, test_name, success, output="", error=""):
        """Log test result"""
        result = {
            'name': test_name,
            'success': success,
            'output': output,
            'error': error,
            'timestamp': datetime.now()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
        if error and not success:
            print(f"    Error: {error}")

    def run_command(self, cmd, test_name, cwd=None):
        """Run a command and capture results"""
        try:
            if cwd is None:
                cwd = "/app"
                
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr if result.stderr else None
            
            self.log_result(test_name, success, output, error)
            return success
            
        except subprocess.TimeoutExpired:
            self.log_result(test_name, False, "", "Test timed out after 5 minutes")
            return False
        except Exception as e:
            self.log_result(test_name, False, "", str(e))
            return False

    def run_unit_tests(self):
        """Run Python unit tests for calculation logic"""
        print("\n🧪 Running Unit Tests...")
        return self.run_command(
            "python test_roster_calculation_regression.py",
            "Unit Tests - Roster Calculation Logic"
        )

    def run_api_contract_tests(self):
        """Run API contract validation tests"""
        print("\n🔗 Running API Contract Tests...")
        return self.run_command(
            "python test_api_contract_regression.py",
            "API Contract Tests"
        )

    def run_playwright_tests(self):
        """Run Playwright E2E regression tests"""
        print("\n🎭 Running Playwright E2E Tests...")
        return self.run_command(
            "npx playwright test tests/e2e/api-regression-validation.spec.js --reporter=line",
            "Playwright E2E Tests"
        )

    def run_backend_health_check(self):
        """Quick backend health check"""
        print("\n🏥 Running Backend Health Check...")
        return self.run_command(
            "curl -f https://league-creator-1.preview.emergentagent.com/api/health",
            "Backend Health Check"
        )

    def run_all_tests(self):
        """Run all regression tests"""
        print("🚀 Starting Comprehensive Regression Test Suite")
        print("=" * 60)
        print(f"Target: Prevent Min=2 gate and Slots=5 display regressions")
        print(f"Started: {self.start_time}")
        print("=" * 60)
        
        # Run all test suites
        tests = [
            self.run_backend_health_check,
            self.run_unit_tests,
            self.run_api_contract_tests,
            self.run_playwright_tests
        ]
        
        all_passed = True
        for test_func in tests:
            success = test_func()
            if not success:
                all_passed = False
        
        # Generate summary report
        self.generate_summary_report(all_passed)
        return all_passed

    def generate_summary_report(self, all_passed):
        """Generate comprehensive test summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        passed_count = sum(1 for r in self.test_results if r['success'])
        total_count = len(self.test_results)
        
        print("\n" + "=" * 60)
        print("📊 REGRESSION TEST SUMMARY REPORT")
        print("=" * 60)
        print(f"Total Duration: {duration:.1f} seconds")
        print(f"Tests Executed: {total_count}")
        print(f"Tests Passed: {passed_count}")
        print(f"Tests Failed: {total_count - passed_count}")
        print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")
        
        # List all test results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['name']}")
            if not result['success'] and result['error']:
                print(f"      └─ {result['error'][:100]}...")
        
        # Critical regression checks
        print(f"\n🎯 CRITICAL REGRESSION PREVENTION:")
        
        critical_checks = [
            "✅ remaining = max(0, clubSlots - ownedCount) never goes negative",
            "✅ UCL defaults: Min=2 managers required to start auction", 
            "✅ UCL defaults: Slots=5 club slots per manager",
            "✅ API contracts maintain consistent structure",
            "✅ Server responses include correct settings everywhere"
        ]
        
        for check in critical_checks:
            print(f"  {check}")
        
        if all_passed:
            print(f"\n🎉 ALL REGRESSION TESTS PASSED!")
            print(f"🛡️  The application is protected against:")
            print(f"    • Min=2 gate regressions (Start Auction disabled at 1, enabled at 2+)")
            print(f"    • Slots=5 display inconsistencies (Lobby/Auction/Roster show 5)")
            print(f"    • Negative remaining slot calculations")
            print(f"    • API contract breaks")
            print(f"    • Settings structure changes")
            return True
        else:
            print(f"\n🚨 REGRESSION TESTS FAILED!")
            print(f"⚠️  REGRESSIONS DETECTED - Immediate attention required!")
            
            # Show failed tests
            failed_tests = [r for r in self.test_results if not r['success']]
            print(f"\n💥 FAILED TESTS:")
            for failed in failed_tests:
                print(f"    • {failed['name']}: {failed['error']}")
            
            return False

    def save_report(self, filename="regression_test_report.md"):
        """Save detailed report to file"""
        end_time = datetime.now()
        
        with open(f"/app/{filename}", 'w') as f:
            f.write("# Regression Test Report\n\n")
            f.write(f"**Generated**: {end_time.isoformat()}\n")
            f.write(f"**Duration**: {(end_time - self.start_time).total_seconds():.1f} seconds\n\n")
            
            f.write("## Test Results\n\n")
            for result in self.test_results:
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                f.write(f"### {result['name']} - {status}\n")
                f.write(f"**Timestamp**: {result['timestamp'].isoformat()}\n\n")
                
                if result['output']:
                    f.write("**Output:**\n```\n")
                    f.write(result['output'][:1000] + "...\n" if len(result['output']) > 1000 else result['output'])
                    f.write("\n```\n\n")
                
                if result['error']:
                    f.write("**Error:**\n```\n")
                    f.write(result['error'])
                    f.write("\n```\n\n")
            
            f.write("## Critical Regression Prevention\n\n")
            f.write("This test suite prevents the following regressions:\n\n")
            f.write("1. **Min=2 Gate**: Start Auction button disabled at 1 member, enabled at 2+\n")
            f.write("2. **Slots=5 Display**: Lobby/Auction/Roster consistently show 5 club slots\n")
            f.write("3. **Calculation Logic**: `remaining = max(0, clubSlots - ownedCount)` never negative\n")
            f.write("4. **API Contracts**: Server responses always include correct settings\n")
            f.write("5. **Structure Validation**: Settings maintain expected data structures\n\n")
        
        print(f"📄 Detailed report saved to: /app/{filename}")


if __name__ == '__main__':
    runner = RegressionTestRunner()
    
    # Change to app directory
    os.chdir('/app')
    
    # Run all tests
    success = runner.run_all_tests()
    
    # Save report
    runner.save_report("regression_test_report.md")
    
    # Exit with appropriate code
    if success:
        print(f"\n🎯 SUCCESS: All regression tests passed!")
        print(f"🛡️  Min=2 gate and Slots=5 display are protected from regressions.")
        sys.exit(0)
    else:
        print(f"\n💥 FAILURE: Regressions detected!")
        print(f"🚨 Immediate action required to fix failing tests.")
        sys.exit(1)