"""
Guardian Backend - Comprehensive Endpoint Verification Script
Tests all API routes and reports results.
"""
import urllib.request
import urllib.error
import json
import sys

BASE = "http://localhost:8000"
RESULTS = []
TOKEN = None
PROJECT_ID = None
SESSION_ID = None
POLICY_ID = None

def req(method, path, data=None, auth=False):
    """Make an HTTP request and return (status, body_dict)."""
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except:
            body = {"detail": str(e)}
        return e.code, body
    except Exception as e:
        return 0, {"detail": str(e)}

def test(name, method, path, data=None, auth=False, expect_status=200):
    status, body = req(method, path, data, auth)
    ok = status == expect_status
    icon = "PASS" if ok else "FAIL"
    RESULTS.append((name, icon, status, expect_status))
    print(f"  [{icon}] {name} -> {status} (expected {expect_status})")
    if not ok and body.get("detail"):
        detail = body["detail"]
        if isinstance(detail, list):
            for d in detail[:2]:
                print(f"         {d}")
        else:
            print(f"         Detail: {detail}")
    return status, body

# ============================================================
# 1. Root
# ============================================================
print("\n=== ROOT ===")
test("GET /", "GET", "/")

# ============================================================
# 2. OpenAPI docs
# ============================================================
print("\n=== DOCS ===")
test("GET /openapi.json", "GET", "/openapi.json")

# ============================================================
# 3. Auth Endpoints
# ============================================================
print("\n=== AUTH ===")
# Register a test user (model requires: username, email, password)
status, body = req("POST", "/api/auth/register", {
    "username": "verifytester",
    "email": "verifytest@guardian.io",
    "password": "TestPass123!"
})
ok = status in (200, 400)
icon = "PASS" if ok else "FAIL"
RESULTS.append(("POST /api/auth/register", icon, status, 200))
print(f"  [{icon}] POST /api/auth/register -> {status} (expected 200 or 400)")
if status == 400:
    print("    (User already exists, proceeding to login)")

# Login (model requires: email, password)
status, body = test("POST /api/auth/login", "POST", "/api/auth/login", {
    "email": "verifytest@guardian.io",
    "password": "TestPass123!"
})
if status == 200:
    TOKEN = body.get("access_token")
    # pyrefly: ignore [unsupported-operation]
    print(f"    Token acquired: {TOKEN[:20]}...")

# Get current user
test("GET /api/auth/me", "GET", "/api/auth/me", auth=True)

# Unauthenticated access should fail
test("GET /api/auth/me (no token)", "GET", "/api/auth/me", auth=False, expect_status=401)

# Verify token
test("GET /api/auth/verify-token", "GET", "/api/auth/verify-token", auth=True)

# Logout
test("POST /api/auth/logout", "POST", "/api/auth/logout")

# Forgot password
test("POST /api/auth/forgot-password", "POST", "/api/auth/forgot-password", {
    "email": "verifytest@guardian.io"
})

# ============================================================
# 4. Project Endpoints
# ============================================================
print("\n=== PROJECTS ===")
# List projects
status, body = test("GET /api/projects", "GET", "/api/projects", auth=True)

# Create project (model requires: name, description; optional: runtime, provider)
status, body = test("POST /api/projects", "POST", "/api/projects", {
    "name": "Verification Test Project",
    "description": "Auto-created by verification script"
}, auth=True, expect_status=201)
if status in (200, 201):
    PROJECT_ID = body.get("id") or body.get("_id")
    print(f"    Project ID: {PROJECT_ID}")

# Get project by ID
if PROJECT_ID:
    test(f"GET /api/projects/{{id}}", "GET", f"/api/projects/{PROJECT_ID}", auth=True)

# ============================================================
# 5. Session Endpoints
# ============================================================
print("\n=== SESSIONS ===")
status, body = test("GET /api/sessions", "GET", "/api/sessions", auth=True)

# Check if /api/sessions/simulate exists
if PROJECT_ID:
    status, body = test("POST /api/sessions/simulate", "POST", "/api/sessions/simulate", {
        "project_id": PROJECT_ID
    }, auth=True, expect_status=201)
    if status in (200, 201):
        SESSION_ID = body.get("session_id") or body.get("id") or body.get("_id")
        print(f"    Session ID: {SESSION_ID}")

# If no session from simulate, grab one from listing
if not SESSION_ID:
    s2, b2 = req("GET", "/api/sessions", auth=True)
    if s2 == 200 and isinstance(b2, list) and len(b2) > 0:
        SESSION_ID = b2[0].get("_id") or b2[0].get("id")
        print(f"    Grabbed existing session: {SESSION_ID}")

if SESSION_ID:
    test(f"GET /api/sessions/{{id}}", "GET", f"/api/sessions/{SESSION_ID}", auth=True)
    test(f"GET /api/sessions/{{id}}/events", "GET", f"/api/sessions/{SESSION_ID}/events", auth=True)

# ============================================================
# 6. Policy Endpoints
# ============================================================
print("\n=== POLICIES ===")
status, body = test("GET /api/policies", "GET", "/api/policies", auth=True)

# Create policy (model requires: name, description; optional: scope, enabled)
status, body = test("POST /api/policies", "POST", "/api/policies", {
    "name": "Verify Test Policy",
    "scope": "global",
    "description": "Auto-created by verification script"
}, auth=True, expect_status=201)
if status in (200, 201):
    POLICY_ID = body.get("id") or body.get("_id")
    print(f"    Policy ID: {POLICY_ID}")

# ============================================================
# 7. Logs Endpoints
# ============================================================
print("\n=== LOGS ===")
test("GET /api/logs", "GET", "/api/logs", auth=True)

# ============================================================
# 8. Risk Events Endpoints
# ============================================================
print("\n=== RISK EVENTS ===")
test("GET /api/risk-events", "GET", "/api/risk-events", auth=True)

# ============================================================
# 9. Analytics Endpoints (actual routes from analytics.py)
# ============================================================
print("\n=== ANALYTICS ===")
test("GET /api/analytics/kpis", "GET", "/api/analytics/kpis", auth=True)
test("GET /api/analytics/charts", "GET", "/api/analytics/charts", auth=True)
test("GET /api/analytics/provider-mix", "GET", "/api/analytics/provider-mix", auth=True)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r[1] == "PASS")
failed = sum(1 for r in RESULTS if r[1] == "FAIL")
total = len(RESULTS)
print(f"SUMMARY: {passed}/{total} passed, {failed} failed")
if failed:
    print("\nFailed tests:")
    for name, icon, status, expected in RESULTS:
        if icon == "FAIL":
            print(f"  - {name}: got {status}, expected {expected}")
else:
    print("\nAll endpoints verified successfully!")
print("=" * 60)
sys.exit(1 if failed else 0)
