import urllib.request
import json

routes = [
    '/',
    '/login',
    '/register',
    '/dashboard',
    '/interview',
    '/feedback',
    '/history',
    '/api/health',
    '/api/jarvis/state',
    '/css/style.css',
    '/css/jarvis.css',
    '/js/main.js',
    '/js/jarvis.js'
]

print("=" * 60)
print("NextHire Live Server Route Verification")
print("=" * 60)

all_ok = True
for r in routes:
    url = f"http://127.0.0.1:5000{r}"
    try:
        req = urllib.request.urlopen(url)
        content_type = req.headers.get("Content-Type", "")
        body = req.read()
        print(f"[OK 200] {r:20} -> Content-Type: {content_type.split(';')[0]:18} Size: {len(body):6} bytes")
    except Exception as e:
        print(f"[FAIL]   {r:20} -> Error: {e}")
        all_ok = False

print("=" * 60)
if all_ok:
    print("ALL ROUTES VERIFIED SUCCESSFULLY (HTTP 200 OK)")
else:
    print("SOME ROUTES FAILED")
print("=" * 60)
