# Amazon Advertising API Setup Guide

## Prerequisites

Before starting, ensure you have:
1. An active Amazon Advertising account
2. Campaign management permissions
3. A valid business use case for API access

## Step 1: Apply for API Access

1. Go to [Amazon Advertising API](https://advertising.amazon.com/API/docs)
2. Sign in with your Amazon Advertising account
3. Navigate to the Advanced Tools Center
4. Choose the appropriate access type:
   - **Self-Serve API Access**: For managing your own campaigns
   - **Advanced API Access**: For agencies or large-scale operations

## Step 2: Create Application & Get Credentials

After approval:

1. Go to the Amazon Developer Console
2. Create a new Security Profile:
   - Name: "AMC Manager Application"
   - Description: "Application for managing AMC instances and queries"
   
3. In the Web Settings tab:
   - Add Allowed Origins: `http://localhost:8000`
   - Add Allowed Return URLs: `http://localhost:8000/api/auth/callback`
   - Note your Client ID and Client Secret

## Step 3: Configure the Application

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your credentials:
   ```env
   # Amazon Advertising API Configuration
   AMAZON_CLIENT_ID=amzn1.application-oa2-client.your-client-id-here
   AMAZON_CLIENT_SECRET=your-client-secret-here
   AMAZON_REDIRECT_URI=http://localhost:8000/api/auth/callback
   AMAZON_SCOPE=cpc_advertising:campaign_management
   ```

## Step 4: Get Profile and Marketplace IDs

After setting up OAuth, you'll need to:

1. Get your Profile ID(s):
   - These represent your advertiser accounts
   - Format: numeric ID like `123456789`

2. Get your Marketplace ID(s):
   - US: `ATVPDKIKX0DER`
   - UK: `A1F83G8C2ARO7P`
   - DE: `A1PA6795UKMFR9`
   - FR: `A13V1IB3VIYZZH`
   - ES: `A1RKKUPIHCS9HS`
   - IT: `APJ6JRA9NG5V4`
   - JP: `A1VC38T7YXB528`
   - CA: `A2EUQ1WTGCTBG2`
   - MX: `A1AM78C64UM0Y8`
   - AU: `A39IBJ37TRP1C6`
   - IN: `A21TJRUUN4KGV`
   - BR: `A2Q3Y263D00KWC`

## Step 5: Test Your Setup

Run the test script:
```bash
python scripts/test_api_connection.py
```

## Troubleshooting

### Common Issues:

1. **"Invalid client" error**
   - Verify Client ID and Secret are correct
   - Ensure redirect URI matches exactly

2. **"Unauthorized" error**
   - Check that your account has API access approved
   - Verify the scopes are correct

3. **"Profile not found"**
   - Ensure you're using the correct Profile ID
   - Verify the profile is active

## Security Best Practices

1. **Never commit credentials**:
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Token Storage**:
   - Tokens are encrypted in the database
   - Refresh tokens regularly

3. **Rate Limiting**:
   - The application handles rate limits automatically
   - Monitor your API usage

## Next Steps

After successful setup:
1. Run database migrations: `alembic upgrade head`
2. Start the application: `python main.py`
3. Navigate to `http://localhost:8000/docs` for API documentation
4. Use `/api/auth/login` to initiate OAuth flow