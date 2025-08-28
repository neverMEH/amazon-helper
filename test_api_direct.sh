#!/bin/bash

# Test the campaign API endpoint directly with curl
echo "Testing Campaign API Endpoint..."
echo "================================"

# You'll need to get a valid auth token from your browser's developer tools
# Open the app, log in, then check Network tab for Authorization header
AUTH_TOKEN="YOUR_AUTH_TOKEN_HERE"

echo "Test 1: Get FEKKAI SP campaigns"
curl -H "Authorization: Bearer $AUTH_TOKEN" \
  "http://localhost:8001/api/campaigns/by-instance-brand/list?instance_id=amccfnbscqp&brand_id=FEKKAI&campaign_type=sponsored_products&limit=3" | python -m json.tool

echo ""
echo "Test 2: Get all FEKKAI campaigns"
curl -H "Authorization: Bearer $AUTH_TOKEN" \
  "http://localhost:8001/api/campaigns/by-instance-brand/list?instance_id=amccfnbscqp&brand_id=FEKKAI&limit=3" | python -m json.tool