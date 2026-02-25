#!/usr/bin/env python3
"""Query NERSC Superfacility API for system status, outages, and metrics."""

import os
import requests
from typing import Optional, List, Dict
from datetime import datetime

try:
    from sfapi_client import Client
    HAS_SFAPI = True
except ImportError:
    HAS_SFAPI = False

# API Base URL
SFAPI_BASE = "https://api.nersc.gov/api/v1.2"


def get_sfapi_client():
    """Create authenticated SF API client."""
    if not HAS_SFAPI:
        raise ImportError("sfapi_client not installed. Run: pip install sfapi_client --user")
    
    client_id = os.getenv("SFAPI_CLIENT_ID")
    key_path = os.getenv("SFAPI_KEY_PATH", "/global/homes/k/kadidia/priv_key.pem")
    
    if not client_id:
        raise ValueError("SFAPI_CLIENT_ID environment variable not set")
    
    with open(os.path.expanduser(key_path), 'r') as f:
        key_content = f.read()
    
    return Client(client_id=client_id, secret=key_content)


# =============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# =============================================================================

def get_all_systems_status() -> List[Dict]:
    """Get status of all NERSC systems using the public status endpoint.
    
    Returns:
        List of dicts with system status info
    """
    try:
        response = requests.get(f"{SFAPI_BASE}/status", timeout=10)
        response.raise_for_status()
        systems = response.json()
        
        results = []
        for system in systems:
            results.append({
                "name": system.get("name", "unknown"),
                "full_name": system.get("full_name", system.get("name", "unknown")),
                "status": system.get("status", "unknown"),
                "description": system.get("description", ""),
                "notes": system.get("notes", []),
                "system_type": system.get("system_type", "")
            })
        
        return results
    
    except Exception as e:
        return [{"error": str(e)}]


def get_all_outages() -> List[Dict]:
    """Get all outages (historical and current).
    
    Returns:
        Flattened list of all outages across all systems
    """
    try:
        response = requests.get(f"{SFAPI_BASE}/status/outages", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # API returns nested lists - flatten them
        outages = []
        for system_outages in data:
            if isinstance(system_outages, list):
                outages.extend(system_outages)
        
        return outages
    
    except Exception as e:
        return [{"error": str(e)}]


def get_planned_outages() -> List[Dict]:
    """Get planned/scheduled outages.
    
    Returns:
        List of planned outages
    """
    try:
        response = requests.get(f"{SFAPI_BASE}/status/outages/planned", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Flatten nested lists
        outages = []
        for system_outages in data:
            if isinstance(system_outages, list):
                outages.extend(system_outages)
        
        return outages
    
    except Exception as e:
        return [{"error": str(e)}]


def get_unplanned_outages() -> List[Dict]:
    """Get unplanned/emergency outages (currently active).
    
    Returns:
        List of unplanned outages (empty if none active)
    """
    try:
        response = requests.get(f"{SFAPI_BASE}/status/outages/unplanned", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Flatten if nested
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            outages = []
            for system_outages in data:
                outages.extend(system_outages)
            return outages
        
        return data if data else []
    
    except Exception as e:
        return [{"error": str(e)}]


def get_recent_outages(days: int = 7) -> List[Dict]:
    """Get outages from the past N days.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of recent outages
    """
    from datetime import timedelta
    
    all_outages = get_all_outages()
    if all_outages and "error" in all_outages[0]:
        return all_outages
    
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for outage in all_outages:
        try:
            start_str = outage.get("start_at", "")
            if start_str:
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                if start_dt.replace(tzinfo=None) >= cutoff:
                    recent.append(outage)
        except (ValueError, TypeError):
            continue
    
    # Sort by start time descending (most recent first)
    recent.sort(key=lambda x: x.get("start_at", ""), reverse=True)
    
    return recent


# =============================================================================
# AUTHENTICATED ENDPOINTS
# =============================================================================

def get_system_status(system: str = "perlmutter") -> Dict:
    """Get current status of a specific NERSC system (authenticated).
    
    Args:
        system: System name (perlmutter, etc.)
    
    Returns:
        dict with name, status, description, notes
    """
    with get_sfapi_client() as client:
        status = client.compute(system)
        return {
            "name": status.name,
            "full_name": getattr(status, 'full_name', status.name),
            "status": str(status.status).replace("StatusValue.", ""),
            "description": status.description,
            "notes": getattr(status, 'notes', [])
        }


# =============================================================================
# FORMATTING HELPERS
# =============================================================================

def format_status_response(result: Dict) -> str:
    """Format status result for Slack/human display."""
    status_indicators = {
        "active": "✅",
        "degraded": "[DEGRADED]",
        "unavailable": "❌",
        "maintenance": "[MAINTENANCE]",
        "unknown": "[UNKNOWN]"
    }
    
    status = result.get("status", "unknown").lower()
    indicator = status_indicators.get(status, "[?]")
    
    response = f"{indicator} *{result.get('name', 'unknown')}*: {result.get('status', 'unknown')}\n"
    if result.get('description'):
        response += f"   {result['description']}"
    
    if result.get('notes'):
        notes = result['notes']
        if isinstance(notes, list) and notes:
            response += "\n   Notes:"
            for note in notes[:2]:
                response += f"\n   - {str(note)[:200]}"
    
    return response


def format_outage(outage: Dict, include_notes: bool = False) -> str:
    """Format a single outage for display."""
    status_indicators = {
        "Planned": "[PLANNED]",
        "Active": "[ACTIVE]",
        "Completed": "✅",
        "Cancelled": "❌"
    }
    
    status = outage.get("status", "Unknown")
    indicator = status_indicators.get(status, "[?]")
    name = outage.get("name", "unknown")
    description = outage.get("description", "No description")
    start = outage.get("start_at", "")[:16].replace("T", " ") if outage.get("start_at") else "?"
    end = outage.get("end_at", "")[:16].replace("T", " ") if outage.get("end_at") else "?"
    swo = outage.get("swo")
    
    result = f"{indicator} *{name}*: {description}\n   {start} -> {end} ({status})"
    
    if swo:
        result += f"\n   SWO: {swo}"
    
    if include_notes and outage.get("notes"):
        result += f"\n   Notes: {outage.get('notes', '')[:200]}"
    
    return result


def is_system_wide_outage(outage: Dict) -> bool:
    """Check if an outage is a System Wide Outage (SWO).
    
    SWOs typically affect Perlmutter or multiple critical systems.
    """
    # Check if SWO field is set
    if outage.get("swo"):
        return True
    
    name = outage.get("name", "").lower()
    description = outage.get("description", "").lower()
    notes = outage.get("notes", "").lower() if outage.get("notes") else ""
    
    # Check for SWO indicators
    swo_keywords = ["system wide", "swo", "full system", "all systems", "perlmutter monthly maintenance"]
    
    combined_text = f"{name} {description} {notes}"
    
    for keyword in swo_keywords:
        if keyword in combined_text:
            return True
    
    # Perlmutter maintenance is typically system-wide
    if name == "perlmutter" and "maintenance" in description:
        return True
    
    return False


def get_system_wide_outages(limit: int = 10) -> List[Dict]:
    """Get System Wide Outages (SWOs).
    
    Args:
        limit: Maximum number of SWOs to return
        
    Returns:
        List of SWO outages, most recent first
    """
    all_outages = get_all_outages()
    
    if all_outages and len(all_outages) > 0 and "error" in all_outages[0]:
        return all_outages
    
    swos = [o for o in all_outages if is_system_wide_outage(o)]
    
    # Sort by start time descending (most recent first)
    swos.sort(key=lambda x: x.get("start_at", ""), reverse=True)
    
    return swos[:limit]


def get_last_swo() -> Optional[Dict]:
    """Get the most recent System Wide Outage.
    
    Returns:
        The most recent SWO or None if none found
    """
    swos = get_system_wide_outages(limit=1)
    
    if swos and len(swos) > 0 and "error" not in swos[0]:
        return swos[0]
    
    return None


# =============================================================================
# MAIN QUERY FUNCTION
# =============================================================================

def query_sfapi(question: str) -> Dict:
    """Main entry point for agent queries about NERSC systems.
    
    Args:
        question: Natural language question about NERSC systems
    
    Returns:
        dict with answer and raw data
    """
    question_lower = question.lower()
    
    try:
        # Check for SWO (System Wide Outage) queries
        if any(word in question_lower for word in ["swo", "system wide outage", "system-wide outage", "systemwide"]):
            # Check if asking for last/most recent SWO
            if any(word in question_lower for word in ["last", "recent", "latest", "previous"]):
                result = get_last_swo()
                if result:
                    formatted = format_outage(result, include_notes=True)
                    return {
                        "source": "sfapi",
                        "answer": f"*Last System Wide Outage:*\n{formatted}",
                        "raw": result
                    }
                else:
                    return {
                        "source": "sfapi",
                        "answer": "No System Wide Outages found in recent history.",
                        "raw": []
                    }
            else:
                # Return list of SWOs
                results = get_system_wide_outages(limit=10)
                if not results:
                    return {
                        "source": "sfapi",
                        "answer": "No System Wide Outages found.",
                        "raw": []
                    }
                formatted = "\n".join([format_outage(o, include_notes=True) for o in results])
                return {
                    "source": "sfapi",
                    "answer": f"*System Wide Outages:*\n{formatted}",
                    "raw": results
                }
        
        # Check for unplanned/emergency outages
        if any(word in question_lower for word in ["unplanned", "emergency", "current outage", "down now"]):
            results = get_unplanned_outages()
            if not results:
                return {
                    "source": "sfapi",
                    "answer": "✅ No unplanned outages currently reported.",
                    "raw": []
                }
            formatted = "\n".join([format_outage(o) for o in results[:5]])
            return {
                "source": "sfapi",
                "answer": f"*Current Unplanned Outages:*\n{formatted}",
                "raw": results
            }
        
        # Check for planned maintenance
        elif any(word in question_lower for word in ["planned", "scheduled", "maintenance", "upcoming"]):
            results = get_planned_outages()
            if not results:
                return {
                    "source": "sfapi",
                    "answer": "No planned maintenance currently scheduled.",
                    "raw": []
                }
            formatted = "\n".join([format_outage(o) for o in results[:10]])
            return {
                "source": "sfapi",
                "answer": f"*Planned Maintenance:*\n{formatted}",
                "raw": results
            }
        
        # Check for recent outages
        elif any(word in question_lower for word in ["recent outage", "last week", "past outage", "history"]):
            results = get_recent_outages(days=7)
            if not results:
                return {
                    "source": "sfapi",
                    "answer": "No outages in the past 7 days.",
                    "raw": []
                }
            formatted = "\n".join([format_outage(o) for o in results[:10]])
            return {
                "source": "sfapi",
                "answer": f"*Recent Outages (past 7 days):*\n{formatted}",
                "raw": results
            }
        
        # Check for all outages
        elif "outage" in question_lower:
            results = get_all_outages()
            # Filter to show only recent/relevant ones
            recent = [o for o in results if o.get("status") in ["Planned", "Active"]][:10]
            if not recent:
                recent = results[:10]  # Show last 10 if no active/planned
            formatted = "\n".join([format_outage(o) for o in recent])
            return {
                "source": "sfapi",
                "answer": f"*Outages:*\n{formatted}",
                "raw": results
            }
        
        # Check for specific system queries
        elif "perlmutter" in question_lower:
            result = get_system_status("perlmutter")
            return {
                "source": "sfapi",
                "answer": format_status_response(result),
                "raw": result
            }
        
        # Check for general status queries
        elif any(word in question_lower for word in ["status", "systems", "up", "down", "running", "available"]):
            results = get_all_systems_status()
            if results and "error" in results[0]:
                return {
                    "source": "sfapi",
                    "answer": f"Error querying status: {results[0]['error']}",
                    "raw": results
                }
            formatted = "\n".join([format_status_response(r) for r in results])
            return {
                "source": "sfapi",
                "answer": f"*NERSC System Status:*\n{formatted}",
                "raw": results
            }
        
        # Default: return all system status
        else:
            results = get_all_systems_status()
            if results and "error" in results[0]:
                return {
                    "source": "sfapi",
                    "answer": f"Error: {results[0]['error']}",
                    "raw": results
                }
            formatted = "\n".join([format_status_response(r) for r in results])
            return {
                "source": "sfapi",
                "answer": formatted,
                "raw": results
            }
    
    except Exception as e:
        return {
            "source": "sfapi",
            "answer": f"Error querying SF API: {str(e)}",
            "raw": {"error": str(e)}
        }


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("NERSC Superfacility API - Comprehensive Test")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("TEST 1: All Systems Status (Public Endpoint)")
    print("=" * 70)
    result = query_sfapi("What is the status of all systems?")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("TEST 2: Perlmutter Status (Authenticated)")
    print("=" * 70)
    result = query_sfapi("What is the status of Perlmutter?")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("TEST 3: Planned Maintenance")
    print("=" * 70)
    result = query_sfapi("What maintenance is planned?")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("TEST 4: Unplanned Outages")
    print("=" * 70)
    result = query_sfapi("Are there any unplanned outages?")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("TEST 5: Recent Outages (Past 7 Days)")
    print("=" * 70)
    result = query_sfapi("What were the recent outages?")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("TEST 6: Last System Wide Outage (SWO)")
    print("=" * 70)
    result = query_sfapi("What was the last SWO?")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("TEST 7: All System Wide Outages")
    print("=" * 70)
    result = query_sfapi("Show me all system wide outages")
    print(result["answer"])
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
