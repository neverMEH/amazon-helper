# AMC API Debugging Guide

Since you can see AMC instances in the UI but our API calls aren't working, here's how to capture the exact API calls:

## Steps to Capture AMC API Calls:

### 1. Open Browser Developer Tools
- Open Chrome/Firefox/Edge
- Press F12 or right-click → "Inspect"
- Go to the "Network" tab

### 2. Access AMC in the Amazon Ads Console
- Log into Amazon Advertising Console
- Navigate to where you see your AMC instances
- Clear the Network tab (🚫 icon)
- Refresh the page or navigate to AMC section

### 3. Look for AMC API Calls
Filter by:
- XHR/Fetch requests only
- Search for keywords: "amc", "instance", "entity"

### 4. Capture Important Details
For each AMC-related request, note:

#### Request URL
- Full endpoint URL
- Query parameters

#### Request Headers
Look especially for:
- `Authorization`
- `Amazon-Advertising-API-*` headers
- Any custom headers
- How entityId is passed

#### Request Method
- GET, POST, etc.

#### Response
- Successful response structure
- How instances are formatted

## Example of What to Look For:

```
Request URL: https://advertising-api.amazon.com/amc/instances?entityId=ENTITY123
Method: GET

Headers:
Authorization: Bearer Atza|...
Amazon-Advertising-API-ClientId: amzn1...
Amazon-Advertising-API-Scope: profileId_or_entityId
X-Amz-Date: 20250728T...
```

## Quick Test Script

Once you capture the exact format, test it with:

```python
import requests

url = "PASTE_EXACT_URL_HERE"
headers = {
    # PASTE EXACT HEADERS HERE
}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())
```

## Common Issues We've Seen:

1. **entityId Format**: The API expects entityId but rejects our format
2. **Missing Headers**: There might be additional required headers
3. **Different Endpoint**: The UI might use a different API version
4. **Authentication Scope**: AMC might need different OAuth scopes

## What We Know So Far:

✅ Your AMC Accounts:
- Recommerce Brands (ENTITYEJZCBSCBH4HZ)
- NeverMeh AMC (ENTITY277TBI8OBF435)

✅ Working Endpoint:
- `/amc/accounts` returns your AMC accounts correctly

❌ Not Working:
- `/amc/instances` with entityId parameter

## Next Steps:

1. Capture the exact API call from the browser
2. Compare headers and parameters
3. Test with the exact same format
4. Update our code with the correct approach

The browser developer tools will show us exactly how Amazon's own UI accesses the AMC instances, which we can then replicate in our code.