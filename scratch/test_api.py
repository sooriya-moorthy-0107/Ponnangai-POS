import urllib.request, urllib.error
req = urllib.request.Request('http://localhost:8000/api/reports/daily?shopkeeper_id=1&start_date=2024-01-01&end_date=2026-12-31')
req.add_header('Cookie', 'session=foo')
try:
    print(urllib.request.urlopen(req).read())
except urllib.error.HTTPError as e:
    print(e.code, e.read())
