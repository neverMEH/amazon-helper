# AMC API Integration Summary

## ✅ What We Successfully Achieved:

### 1. **OAuth Authentication Working**
- Successfully authenticated with Amazon Advertising API
- Obtained access and refresh tokens
- Retrieved 13 advertising profiles

### 2. **AMC Accounts Discovery**
- Successfully called `/amc/accounts` endpoint
- Found 2 AMC accounts:
  - **Recommerce Brands** (ENTITYEJZCBSCBH4HZ)
  - **NeverMeh AMC** (ENTITY277TBI8OBF435)

### 3. **Working Code Structure**
```python
# This works - gets AMC accounts
headers = {
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-ClientId': client_id,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

response = requests.get('https://advertising-api.amazon.com/amc/accounts', headers=headers)
# Returns: {"amcAccounts": [{"accountId": "ENTITY...", "accountName": "...", "marketplaceId": "..."}]}
```

## ❌ The Problem: AMC Instances

The `/amc/instances` endpoint consistently returns:
```json
{"code": "400", "details": "entityId provided is null"}
```

We tried passing entityId as:
- Query parameter: `?entityId=ENTITY...`
- Various header formats
- POST body
- Different parameter names

## 🔍 Root Cause Analysis:

1. **The AMC instances API might use a different format** than documented
2. **Additional permissions/scopes might be required**
3. **The UI might use internal/undocumented APIs**

## 📋 Action Items:

### 1. **Capture the Actual API Call**
Since you can see AMC instances in the UI:

1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Navigate to AMC instances in Amazon Ads Console
4. Look for API calls containing "instance"
5. Right-click the request → Copy → Copy as cURL

### 2. **Check for Different Base URLs**
The UI might use:
- A different subdomain (not `advertising-api.amazon.com`)
- An internal API endpoint
- A regional endpoint

### 3. **Verify OAuth Scopes**
Current scope: `advertising::campaign_management`

The UI might use additional scopes like:
- `advertising::amc::read`
- `advertising::amc::manage`
- Or other AMC-specific scopes

## 🚀 Next Steps:

### Option 1: Browser DevTools (Recommended)
1. Capture the exact API call from the browser
2. Share the request details (with sensitive data redacted)
3. I'll update the code to match exactly

### Option 2: Contact Amazon Support
1. Ask specifically about the `/amc/instances` endpoint
2. Request documentation for the `entityId` parameter format
3. Confirm if additional OAuth scopes are needed

### Option 3: Use What Works
While we figure out instances, you can:
1. Use the AMC account information we retrieved
2. Build the query builder and workflow components
3. Add instance management later when we solve the API issue

## 💾 Your Current Setup:

### Credentials (Working ✅)
- Client ID: `amzn1.application-oa2-client.cf1789da23f74ee489e2373e424726af`
- Tokens: Stored in `tokens.json`
- Profiles: 13 profiles across US, CA, MX

### AMC Accounts (Found ✅)
- Recommerce Brands (ENTITYEJZCBSCBH4HZ)
- NeverMeh AMC (ENTITY277TBI8OBF435)

### Application Structure (Ready ✅)
- Complete FastAPI backend
- Database models
- Service layers
- Query builder with templates

## 📝 Code to Refresh Token:
```python
# When you need to refresh the token
python refresh_and_explore.py
```

The application architecture is solid and ready. We just need to solve the AMC instances API format issue.