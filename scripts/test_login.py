import urllib.request
import json

base = "http://127.0.0.1:8001"

req = urllib.request.Request(
    f"{base}/api/auth/login",
    data=json.dumps({"username": "admin", "password": "changeme"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print("login response:", data)
    token = data.get("token")
    if not token:
        raise SystemExit("API did not return token — restart uvicorn to load latest code")
    print("login ok:", data["username"])

req2 = urllib.request.Request(
    f"{base}/api/auth/me",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    print("me ok:", json.loads(resp.read()))
