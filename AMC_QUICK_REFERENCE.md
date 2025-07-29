# AMC Quick Reference Guide

## Key Discovery
✅ **SOLVED**: Pass entity ID as `Amazon-Advertising-API-AdvertiserId` header, not as query parameter!

## Authentication Flow
1. Get authorization code from user
2. Exchange for access/refresh tokens
3. Use tokens to get advertising profiles
4. Use profile entity IDs to get AMC instances

## Important AMC Instances

### Sandbox Instances (for testing)
1. **Recommerce Brands Sandbox**
   - Instance ID: `amchnfozgta`
   - Instance Name: `recommercebrandssandbox`
   - Perfect for testing queries and workflows

2. **NeverMeh AMC Sandbox**
   - Instance ID: `amcfo8abayq`
   - Instance Name: `nevermehamcsandbox`

### Major Brand Instances
1. **Supergoop US** - `amcibersblt`
2. **Shiseido US** - `amc6ikpceyf`
3. **Fekkai US** - `amccfnbscqp`
4. **Solgar US** - `amczj5bslba`
5. **Drunk Elephant US** - `amcgjj6iu5v`

## API Endpoints
- Base URL: `https://advertising-api.amazon.com`
- Instances: `/amc/instances?nextToken=`
- Workflows: `/amc/instances/{instanceId}/workflows`
- Executions: `/amc/instances/{instanceId}/executions`

## Required Headers
```python
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-MarketplaceId': 'ATVPDKIKX0DER',
    'Amazon-Advertising-API-AdvertiserId': ENTITY_ID  # Critical!
}
```

## Common AMC SQL Query Templates
1. **Path to Conversion** - Analyze customer journey
2. **New-to-Brand** - Find new customers
3. **Audience Overlap** - Compare audience segments
4. **Campaign Performance** - Detailed campaign metrics
5. **ASIN Performance** - Product-level analytics

## Instance Capabilities
All instances have these activated features:
- Conversions tracking (V2/V3)
- Sponsored Ads data
- Portfolio management
- Creative/ASIN level data
- Audience safety features
- Frequency groups

## Testing Workflow
1. Use sandbox instance for development
2. Create test workflow with simple query
3. Execute and monitor results
4. Promote to production instance