"""Test Dhan API directly to verify credentials"""
import httpx
import json

# Your credentials
CLIENT_ID = "1112957731"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzg1ODY2OTcxLCJpYXQiOjE3ODU3ODA1NzEsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTEyOTU3NzMxIn0.MxCOjMsWf414uJPsjFdWqm1jsEufrwV1PfoE5ROKSleZwld2O_5ZCwRDXB4tIHVUeLB11-DZUUV-8oG3nTdb6A"
API_KEY = "f9386b6a"
API_SECRET = "8b81fa60-0510-4169-8ddb-d5ea30734974"

print("=== Testing Dhan Data API ===\n")

# Test 1: Current method (JWT only)
print("1. Testing with JWT only (current method):")
headers1 = {
    "access-token": ACCESS_TOKEN,
    "client-id": CLIENT_ID,
    "Content-Type": "application/json",
}
body = {"NSE_EQ": [2885]}  # RELIANCE
try:
    r = httpx.post("https://api.dhan.co/v2/marketfeed/quote", json=body, headers=headers1, timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Response: {json.dumps(data, indent=2)[:300]}")
    else:
        print(f"   Error: {r.text[:200]}")
except Exception as e:
    print(f"   Exception: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Try with API Key in headers (some APIs use this)
print("2. Testing with API Key in headers:")
headers2 = {
    "access-token": ACCESS_TOKEN,
    "client-id": CLIENT_ID,
    "api-key": API_KEY,
    "Content-Type": "application/json",
}
try:
    r = httpx.post("https://api.dhan.co/v2/marketfeed/quote", json=body, headers=headers2, timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Response: {json.dumps(data, indent=2)[:300]}")
    else:
        print(f"   Error: {r.text[:200]}")
except Exception as e:
    print(f"   Exception: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Check token expiry
print("3. Checking JWT token expiry:")
import base64
import time as tm
parts = ACCESS_TOKEN.split('.')
if len(parts) >= 2:
    pad = parts[1] + '=' * (-len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(pad))
    exp = payload.get('exp', 0)
    now = int(tm.time())
    print(f"   Token expires at: {exp}")
    print(f"   Current time: {now}")
    print(f"   Time until expiry: {exp - now} seconds ({(exp - now) / 3600:.1f} hours)")
    print(f"   Token valid: {'YES' if exp > now else 'NO - EXPIRED!'}")

print("\n" + "="*50)
print("\nDONE. Check results above.")
