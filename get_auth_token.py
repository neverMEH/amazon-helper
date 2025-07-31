#!/usr/bin/env python3
"""Get auth token for testing"""

import requests

# Login
response = requests.post(
    'http://localhost:8001/api/auth/login',
    params={'email': 'nick@nevermeh.com', 'password': ''}
)

if response.status_code == 200:
    data = response.json()
    print(f"Token: {data['access_token']}")
    print(f"\nTo test workflows API:")
    print(f"curl http://localhost:8001/api/workflows/ -H 'Authorization: Bearer {data['access_token']}'")
else:
    print(f"Login failed: {response.status_code}")
    print(response.text)