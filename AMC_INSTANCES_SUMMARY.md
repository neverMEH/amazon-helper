# AMC Instances Discovery Summary

## Key Discovery
The AMC instances API requires the entity ID to be passed as a **header**, not as a query parameter. This was the crucial missing piece that was causing "entityId provided is null" errors.

### Correct API Format
```bash
curl --location 'https://advertising-api.amazon.com/amc/instances?nextToken=' \
  --header 'Amazon-Advertising-API-ClientId: {CLIENT_ID}' \
  --header 'Authorization: Bearer {ACCESS_TOKEN}' \
  --header 'Amazon-Advertising-API-MarketplaceId: ATVPDKIKX0DER' \
  --header 'Amazon-Advertising-API-AdvertiserId: {ENTITY_ID}'  # <-- This is the key!
```

## AMC Accounts Found
1. **Recommerce Brands** (ENTITYEJZCBSCBH4HZ) - US Marketplace
   - 50 AMC instances (49 STANDARD, 1 SANDBOX)
   - Various brands including Supergoop, Terry Naturally, Fekkai, etc.

2. **NeverMeh AMC** (ENTITY277TBI8OBF435) - US Marketplace
   - 8 AMC instances (7 STANDARD, 1 SANDBOX)
   - Brands include Dirty Labs, EMF Harmony, Typhoon Helmets, Defender Operations, Desert Fox Golf, and Panera DSP

## AMC Instance Structure
Each AMC instance contains:
- `instanceId`: Unique identifier (e.g., "amcibersblt")
- `instanceName`: Human-readable name (e.g., "recommercesupergoopus")
- `instanceType`: STANDARD or SANDBOX
- `customerCanonicalName`: Brand name (e.g., "Supergoop US")
- `creationStatus`: COMPLETED
- `s3BucketName`: S3 bucket for data storage
- `apiEndpoint`: https://advertising-api.amazon.com
- `entities`: Array of entity IDs (usually ["NA"])
- `optionalDatasets`: Array of activated features with timestamps

## Notable Instances
1. **Sandbox Instance**: `amchnfozgta` - "recommercebrandssandbox" for testing
2. **Production Instances**: 49 standard instances for various brands

## Optional Datasets (Features)
Common features activated across instances:
- CONVERSIONS_V2 / CONVERSIONS_EXPOSURE_V3
- CASPIAN_DIM_CUTOVER / CASPIAN_FACT_CUTOVER
- PRE_VALIDATED_OBSIDIAN / PRE_VALIDATED_SPONSORED_ADS
- SNS_V2 / SNS_BROADCAST_JOIN_FIX
- PORTFOLIOS / CREATIVE_ASIN
- FREQUENCY_GROUPS
- AUDIENCES_ASIN_SAFETY_V2

## Summary Statistics
- **Total AMC Instances**: 58
- **Standard Instances**: 56
- **Sandbox Instances**: 2 (one for each account)
- **Recommerce Brands Instances**: 50
- **NeverMeh AMC Instances**: 8

## Next Steps
1. ✅ Update the application code to use correct headers (completed)
2. ✅ Run the script for both AMC entities (completed)
3. Implement workflow creation and query execution for these instances
4. Set up PostgreSQL database and run migrations
5. Build UI to display and manage instances
6. Implement query templates for common use cases
7. Add campaign ID mapping functionality
8. Set up scheduling system for recurring reports

## Files Created
- `amc_instances_ENTITYEJZCBSCBH4HZ.json` - Full response for Recommerce Brands
- `amc_complete_summary.json` - Summary of all instances (will be created after running for both entities)
- `amc_instances_working.py` - Working script to retrieve AMC instances