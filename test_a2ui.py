"""
A2UI Dynamic Engine Verification Suite
Tests the new 'data_view' generic logic.
"""
import requests
import json

BASE = "http://localhost:8000"
SESSION = "dynamic_engine_test"
HEADERS = {"Origin": "http://localhost:5173"}

test_cases = [
    {"name": "GREETING", "query": "Hello there!", "expect_data_view": False},
    {"name": "DYNAMIC SKILLS", "query": "What are your top technical skills?", "expect_data_view": True},
    {"name": "DYNAMIC PROJECTS", "query": "Tell me about your portfolio projects", "expect_data_view": True},
    {"name": "NON-PORTFOLIO", "query": "Tell me about 3 popular programming languages.", "expect_data_view": True},
]

print(f"{'TEST NAME':<15} | {'QUERY':<40} | {'STATUS':<10}")
print("-" * 80)

for case in test_cases:
    try:
        r = requests.post(
            f"{BASE}/chat", 
            json={"message": case["query"], "session_id": SESSION},
            headers=HEADERS,
            timeout=35
        )
        data = r.json()
        
        chunks = data.get("chunks", [])
        has_data_view = any(c["type"] == "a2ui" and "data_view" in c["content"] for c in chunks)
        
        status = "PASS" if has_data_view == case["expect_data_view"] else "FAIL"
        
        print(f"{case['name']:<15} | {case['query']:<40} | {status:<10}")
        
    except Exception as e:
        print(f"{case['name']:<15} | {case['query']:<40} | ERROR      | {str(e)[:25]}")

print("-" * 80)
