#!/usr/bin/env python3
"""Unit tests for NERSC Superfacility API functions."""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_sfapi import (
    get_all_systems_status,
    get_all_outages,
    get_planned_outages,
    get_unplanned_outages,
    get_recent_outages,
    get_system_status,
    get_system_wide_outages,
    get_last_swo,
    is_system_wide_outage,
    format_status_response,
    format_outage,
    query_sfapi,
    HAS_SFAPI
)


class Colors:
    """Terminal colors for pretty output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")


def print_pass(test_name: str, details: str = ""):
    """Print a passing test."""
    print(f"{Colors.GREEN}✅ PASS:{Colors.RESET} {test_name}")
    if details:
        print(f"   {Colors.YELLOW}{details}{Colors.RESET}")


def print_fail(test_name: str, error: str):
    """Print a failing test."""
    print(f"{Colors.RED}❌ FAIL:{Colors.RESET} {test_name}")
    print(f"   {Colors.RED}Error: {error}{Colors.RESET}")


def print_skip(test_name: str, reason: str):
    """Print a skipped test."""
    print(f"{Colors.YELLOW}-- SKIP:{Colors.RESET} {test_name}")
    print(f"   {Colors.YELLOW}Reason: {reason}{Colors.RESET}")


# =============================================================================
# TEST: get_all_systems_status()
# =============================================================================

def test_get_all_systems_status():
    """Test fetching all system statuses."""
    print_header("TEST: get_all_systems_status()")
    
    try:
        results = get_all_systems_status()
        
        # Check it returns a list
        assert isinstance(results, list), "Should return a list"
        print_pass("Returns a list", f"Got {len(results)} systems")
        
        # Check for errors
        if results and "error" in results[0]:
            print_fail("No errors", results[0]["error"])
            return False
        print_pass("No errors in response")
        
        # Check structure of first result
        if results:
            first = results[0]
            required_fields = ["name", "status"]
            for field in required_fields:
                assert field in first, f"Missing field: {field}"
            print_pass("Has required fields", f"Fields: {list(first.keys())}")
            
        # Print sample data
            print(f"\n   {Colors.BLUE}Sample systems:{Colors.RESET}")
            for system in results[:5]:
                print(f"   - {system.get('name')}: {system.get('status')}")
        
        return True
        
    except Exception as e:
        print_fail("get_all_systems_status()", str(e))
        return False


# =============================================================================
# TEST: get_all_outages()
# =============================================================================

def test_get_all_outages():
    """Test fetching all outages."""
    print_header("TEST: get_all_outages()")
    
    try:
        results = get_all_outages()
        
        # Check it returns a list
        assert isinstance(results, list), "Should return a list"
        print_pass("Returns a list", f"Got {len(results)} outages")
        
        # Check for errors
        if results and "error" in results[0]:
            print_fail("No errors", results[0]["error"])
            return False
        print_pass("No errors in response")
        
        # Check structure
        if results:
            first = results[0]
            required_fields = ["name", "start_at", "status"]
            for field in required_fields:
                assert field in first, f"Missing field: {field}"
            print_pass("Has required fields", f"Fields: {list(first.keys())}")
            
            # Count by status
            status_counts = {}
            for outage in results:
                status = outage.get("status", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            print(f"\n   {Colors.BLUE}Outages by status:{Colors.RESET}")
            for status, count in status_counts.items():
                print(f"   - {status}: {count}")
        
        return True
        
    except Exception as e:
        print_fail("get_all_outages()", str(e))
        return False


# =============================================================================
# TEST: get_planned_outages()
# =============================================================================

def test_get_planned_outages():
    """Test fetching planned outages."""
    print_header("TEST: get_planned_outages()")
    
    try:
        results = get_planned_outages()
        
        # Check it returns a list
        assert isinstance(results, list), "Should return a list"
        print_pass("Returns a list", f"Got {len(results)} planned outages")
        
        # Check for errors
        if results and len(results) > 0 and isinstance(results[0], dict) and "error" in results[0]:
            print_fail("No errors", results[0]["error"])
            return False
        print_pass("No errors in response")
        
        # Verify all are planned status
        if results:
            all_planned = all(o.get("status") == "Planned" for o in results)
            if all_planned:
                print_pass("All outages have 'Planned' status")
            else:
                statuses = set(o.get("status") for o in results)
                print_fail("All planned status", f"Found statuses: {statuses}")
            
            # Print upcoming maintenance
            print(f"\n   {Colors.BLUE}Upcoming maintenance:{Colors.RESET}")
            for outage in results[:5]:
                print(f"   - {outage.get('name')}: {outage.get('description', 'N/A')}")
                print(f"     {outage.get('start_at', '?')[:16]} → {outage.get('end_at', '?')[:16]}")
        else:
            print(f"   {Colors.YELLOW}No planned outages currently scheduled{Colors.RESET}")
        
        return True
        
    except Exception as e:
        print_fail("get_planned_outages()", str(e))
        return False


# =============================================================================
# TEST: get_unplanned_outages()
# =============================================================================

def test_get_unplanned_outages():
    """Test fetching unplanned outages."""
    print_header("TEST: get_unplanned_outages()")
    
    try:
        results = get_unplanned_outages()
        
        # Check it returns a list
        assert isinstance(results, list), "Should return a list"
        print_pass("Returns a list", f"Got {len(results)} unplanned outages")
        
        # Check for errors
        if results and len(results) > 0 and isinstance(results[0], dict) and "error" in results[0]:
            print_fail("No errors", results[0]["error"])
            return False
        print_pass("No errors in response")
        
        if results:
            print(f"\n   {Colors.RED}Active unplanned outages:{Colors.RESET}")
            for outage in results[:5]:
                print(f"   - {outage.get('name')}: {outage.get('description', 'N/A')}")
        else:
            print(f"   {Colors.GREEN}No unplanned outages - all systems normal!{Colors.RESET}")
        
        return True
        
    except Exception as e:
        print_fail("get_unplanned_outages()", str(e))
        return False


# =============================================================================
# TEST: get_recent_outages()
# =============================================================================

def test_get_recent_outages():
    """Test fetching recent outages."""
    print_header("TEST: get_recent_outages(days=7)")
    
    try:
        results = get_recent_outages(days=7)
        
        # Check it returns a list
        assert isinstance(results, list), "Should return a list"
        print_pass("Returns a list", f"Got {len(results)} recent outages")
        
        # Check for errors
        if results and len(results) > 0 and isinstance(results[0], dict) and "error" in results[0]:
            print_fail("No errors", results[0]["error"])
            return False
        print_pass("No errors in response")
        
        # Verify dates are within range
        if results:
            cutoff = datetime.now() - timedelta(days=7)
            all_recent = True
            for outage in results:
                start_str = outage.get("start_at", "")
                if start_str:
                    try:
                        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        if start_dt.replace(tzinfo=None) < cutoff:
                            all_recent = False
                            break
                    except:
                        pass
            
            if all_recent:
                print_pass("All outages within 7 days")
            else:
                print_fail("Date filtering", "Some outages outside 7-day window")
            
            # Print recent outages
            print(f"\n   {Colors.BLUE}Recent outages:{Colors.RESET}")
            for outage in results[:5]:
                print(f"   - {outage.get('name')}: {outage.get('description', 'N/A')[:50]}")
                print(f"     Status: {outage.get('status')} | {outage.get('start_at', '?')[:10]}")
        else:
            print(f"   {Colors.GREEN}No outages in the past 7 days{Colors.RESET}")
        
        return True
        
    except Exception as e:
        print_fail("get_recent_outages()", str(e))
        return False


# =============================================================================
# TEST: get_system_status() - Authenticated
# =============================================================================

def test_get_system_status():
    """Test fetching specific system status (authenticated)."""
    print_header("TEST: get_system_status('perlmutter') [Authenticated]")
    
    # Check prerequisites
    if not HAS_SFAPI:
        print_skip("get_system_status()", "sfapi_client not installed")
        return None
    
    client_id = os.getenv("SFAPI_CLIENT_ID")
    if not client_id:
        print_skip("get_system_status()", "SFAPI_CLIENT_ID not set")
        return None
    
    key_path = os.getenv("SFAPI_KEY_PATH", "/global/homes/k/kadidia/priv_key.pem")
    if not os.path.exists(os.path.expanduser(key_path)):
        print_skip("get_system_status()", f"Key file not found: {key_path}")
        return None
    
    try:
        result = get_system_status("perlmutter")
        
        # Check it returns a dict
        assert isinstance(result, dict), "Should return a dict"
        print_pass("Returns a dict")
        
        # Check required fields
        required_fields = ["name", "status", "description"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        print_pass("Has required fields", f"Fields: {list(result.keys())}")
        
        # Print status
        print(f"\n   {Colors.BLUE}Perlmutter Status:{Colors.RESET}")
        print(f"   - Name: {result.get('name')}")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Description: {result.get('description')}")
        
        return True
        
    except Exception as e:
        print_fail("get_system_status()", str(e))
        return False


# =============================================================================
# TEST: get_system_wide_outages()
# =============================================================================

def test_get_system_wide_outages():
    """Test fetching System Wide Outages (SWOs)."""
    print_header("TEST: get_system_wide_outages()")
    
    try:
        results = get_system_wide_outages(limit=10)
        
        # Check it returns a list
        assert isinstance(results, list), "Should return a list"
        print_pass("Returns a list", f"Got {len(results)} SWOs")
        
        # Check for errors
        if results and len(results) > 0 and isinstance(results[0], dict) and "error" in results[0]:
            print_fail("No errors", results[0]["error"])
            return False
        print_pass("No errors in response")
        
        if results:
            # Verify these are actually SWOs
            print(f"\n   {Colors.BLUE}System Wide Outages:{Colors.RESET}")
            for outage in results[:5]:
                print(f"   - {outage.get('name')}: {outage.get('description', 'N/A')[:50]}")
                print(f"     {outage.get('start_at', '?')[:10]} | Status: {outage.get('status')}")
        else:
            print(f"   {Colors.YELLOW}No SWOs found in history{Colors.RESET}")
        
        return True
        
    except Exception as e:
        print_fail("get_system_wide_outages()", str(e))
        return False


# =============================================================================
# TEST: get_last_swo()
# =============================================================================

def test_get_last_swo():
    """Test fetching the last System Wide Outage."""
    print_header("TEST: get_last_swo()")
    
    try:
        result = get_last_swo()
        
        if result is None:
            print_pass("Returns None when no SWOs", "No SWOs in history")
            return True
        
        # Check it returns a dict
        assert isinstance(result, dict), "Should return a dict"
        print_pass("Returns a dict")
        
        # Check required fields
        required_fields = ["name", "start_at", "status"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        print_pass("Has required fields")
        
        # Print the last SWO
        print(f"\n   {Colors.BLUE}Last SWO:{Colors.RESET}")
        print(f"   - System: {result.get('name')}")
        print(f"   - Description: {result.get('description', 'N/A')}")
        print(f"   - Start: {result.get('start_at', '?')[:16]}")
        print(f"   - End: {result.get('end_at', '?')[:16]}")
        print(f"   - Status: {result.get('status')}")
        
        return True
        
    except Exception as e:
        print_fail("get_last_swo()", str(e))
        return False


# =============================================================================
# TEST: is_system_wide_outage()
# =============================================================================

def test_is_system_wide_outage():
    """Test SWO detection logic."""
    print_header("TEST: is_system_wide_outage()")
    
    try:
        # Test Perlmutter maintenance (should be SWO)
        perlmutter_maintenance = {
            "name": "perlmutter",
            "description": "Perlmutter Monthly Maintenance",
            "status": "Planned"
        }
        assert is_system_wide_outage(perlmutter_maintenance) == True, "Perlmutter maintenance should be SWO"
        print_pass("Perlmutter maintenance detected as SWO")
        
        # Test explicit SWO field
        explicit_swo = {
            "name": "perlmutter",
            "description": "Some outage",
            "swo": "SWO-12345"
        }
        assert is_system_wide_outage(explicit_swo) == True, "Explicit SWO field should be detected"
        print_pass("Explicit SWO field detected")
        
        # Test non-SWO outage
        jupyter_outage = {
            "name": "jupyter",
            "description": "Jupyter is down",
            "status": "Completed"
        }
        assert is_system_wide_outage(jupyter_outage) == False, "Jupyter outage should not be SWO"
        print_pass("Non-SWO outage correctly identified")
        
        # Test system-wide keywords
        system_wide_outage = {
            "name": "network",
            "description": "System wide network issue",
            "status": "Active"
        }
        assert is_system_wide_outage(system_wide_outage) == True, "System wide keyword should be SWO"
        print_pass("'System wide' keyword detected as SWO")
        
        return True
        
    except AssertionError as e:
        print_fail("is_system_wide_outage()", str(e))
        return False
    except Exception as e:
        print_fail("is_system_wide_outage()", str(e))
        return False


# =============================================================================
# TEST: format_status_response()
# =============================================================================

def test_format_status_response():
    """Test status formatting."""
    print_header("TEST: format_status_response()")
    
    try:
        # Test active status
        test_data = {
            "name": "perlmutter",
            "status": "active",
            "description": "System is active"
        }
        result = format_status_response(test_data)
        
        assert "✅" in result, "Should have checkmark emoji for active"
        assert "perlmutter" in result, "Should contain system name"
        print_pass("Active status formatting", "Contains ✅ emoji")
        
        # Test degraded status
        test_data["status"] = "degraded"
        result = format_status_response(test_data)
        assert "⚠️" in result, "Should have warning emoji for degraded"
        print_pass("Degraded status formatting", "Contains ⚠️ emoji")
        
        # Test unavailable status
        test_data["status"] = "unavailable"
        result = format_status_response(test_data)
        assert "❌" in result, "Should have X emoji for unavailable"
        print_pass("Unavailable status formatting", "Contains ❌ emoji")
        
        return True
        
    except Exception as e:
        print_fail("format_status_response()", str(e))
        return False


# =============================================================================
# TEST: format_outage()
# =============================================================================

def test_format_outage():
    """Test outage formatting."""
    print_header("TEST: format_outage()")
    
    try:
        # Test planned outage
        test_data = {
            "name": "perlmutter",
            "description": "Monthly Maintenance",
            "start_at": "2026-03-18T06:00:00",
            "end_at": "2026-03-18T22:00:00",
            "status": "Planned"
        }
        result = format_outage(test_data)
        
        assert "📅" in result, "Should have calendar emoji for planned"
        assert "perlmutter" in result, "Should contain system name"
        assert "Monthly Maintenance" in result, "Should contain description"
        print_pass("Planned outage formatting", "Contains 📅 emoji")
        
        # Test completed outage
        test_data["status"] = "Completed"
        result = format_outage(test_data)
        assert "✅" in result, "Should have checkmark emoji for completed"
        print_pass("Completed outage formatting", "Contains ✅ emoji")
        
        # Test active outage
        test_data["status"] = "Active"
        result = format_outage(test_data)
        assert "🔴" in result, "Should have red circle for active"
        print_pass("Active outage formatting", "Contains 🔴 emoji")
        
        return True
        
    except Exception as e:
        print_fail("format_outage()", str(e))
        return False


# =============================================================================
# TEST: query_sfapi() - Natural Language Queries
# =============================================================================

def test_query_sfapi():
    """Test natural language query interface."""
    print_header("TEST: query_sfapi() - Natural Language Queries")
    
    test_queries = [
        ("What is the status of all systems?", "status"),
        ("What maintenance is planned?", "planned"),
        ("Are there any unplanned outages?", "unplanned"),
        ("What were the recent outages?", "recent"),
        ("Is Perlmutter running?", "perlmutter"),
        ("What was the last SWO?", "swo"),
        ("Show me system wide outages", "swo"),
    ]
    
    all_passed = True
    
    for query, expected_type in test_queries:
        try:
            result = query_sfapi(query)
            
            # Check structure
            assert isinstance(result, dict), "Should return a dict"
            assert "source" in result, "Should have 'source' field"
            assert "answer" in result, "Should have 'answer' field"
            assert "raw" in result, "Should have 'raw' field"
            assert result["source"] == "sfapi", "Source should be 'sfapi'"
            
            print_pass(f"Query: '{query[:40]}...'", f"Got answer ({len(result['answer'])} chars)")
            
        except Exception as e:
            print_fail(f"Query: '{query[:40]}...'", str(e))
            all_passed = False
    
    return all_passed


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all unit tests."""
    print(f"\n{Colors.BOLD}{'#' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}# NERSC Superfacility API - Unit Tests{Colors.RESET}")
    print(f"{Colors.BOLD}# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{'#' * 70}{Colors.RESET}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Run tests
    tests = [
        ("get_all_systems_status", test_get_all_systems_status),
        ("get_all_outages", test_get_all_outages),
        ("get_planned_outages", test_get_planned_outages),
        ("get_unplanned_outages", test_get_unplanned_outages),
        ("get_recent_outages", test_get_recent_outages),
        ("get_system_wide_outages", test_get_system_wide_outages),
        ("get_last_swo", test_get_last_swo),
        ("is_system_wide_outage", test_is_system_wide_outage),
        ("get_system_status", test_get_system_status),
        ("format_status_response", test_format_status_response),
        ("format_outage", test_format_outage),
        ("query_sfapi", test_query_sfapi),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result is True:
                results["passed"] += 1
            elif result is False:
                results["failed"] += 1
            elif result is None:
                results["skipped"] += 1
        except Exception as e:
            print_fail(name, str(e))
            results["failed"] += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
    print(f"{'=' * 70}")
    print(f"{Colors.GREEN}Passed:  {results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed:  {results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped: {results['skipped']}{Colors.RESET}")
    print(f"{'=' * 70}")
    
    total = results['passed'] + results['failed']
    if total > 0:
        pct = (results['passed'] / total) * 100
        if pct == 100:
            print(f"{Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.RESET}")
        elif pct >= 80:
            print(f"{Colors.YELLOW}{pct:.0f}% tests passed{Colors.RESET}")
        else:
            print(f"{Colors.RED}{pct:.0f}% tests passed{Colors.RESET}")
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
