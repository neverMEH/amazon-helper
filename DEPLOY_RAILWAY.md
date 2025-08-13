# Deploying to Railway

This guide will help you deploy the AMC Manager application to Railway.app.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional, for local deployment)
3. A GitHub account (for automatic deployments)

## Environment Variables

You'll need to set these environment variables in Railway:

```bash
# Required - From your .env file
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Optional - Amazon API credentials (if using real API)
AMAZON_CLIENT_ID=your_client_id
AMAZON_CLIENT_SECRET=your_client_secret

# Railway will automatically set PORT
```

## Deployment Methods

### Method 1: Deploy from GitHub (Recommended)

1. Push your code to a GitHub repository
2. In Railway dashboard:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the configuration

3. Add environment variables:
   - Click on your service
   - Go to "Variables" tab
   - Add all required environment variables

4. Railway will automatically:
   - Install dependencies
   - Build the frontend
   - Start the backend server
   - Provide a public URL

### Method 2: Deploy from CLI

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Initialize project:
   ```bash
   railway init
   ```

4. Link to a new project:
   ```bash
   railway link
   ```

5. Add environment variables:
   ```bash
   railway variables set SUPABASE_URL=your_url
   railway variables set SUPABASE_ANON_KEY=your_key
   railway variables set SUPABASE_SERVICE_ROLE_KEY=your_service_key
   ```

6. Deploy:
   ```bash
   railway up
   ```

### Method 3: Deploy via Railway Dashboard

1. Go to https://dashboard.railway.app
2. Click "New Project" → "Empty Project"
3. Click "Add Service" → "GitHub Repo" or "Empty Service"
4. If empty service, use Railway CLI to push code
5. Add environment variables in the Variables tab

## Post-Deployment

1. **Run Database Migration**:
   - Copy the SQL from `database/supabase/migrations/02_instance_brands.sql`
   - Run it in your Supabase SQL editor

2. **Access Your App**:
   - Railway will provide a URL like: `https://your-app.up.railway.app`
   - Login with: nick@nevermeh.com

3. **Monitor Logs**:
   - Click on your service in Railway
   - Go to "Logs" tab to see real-time logs

## Troubleshooting

1. **Build Failures**:
   - Check the build logs in Railway
   - Ensure all dependencies are in requirements_supabase.txt
   - Verify nixpacks.toml configuration

2. **Runtime Errors**:
   - Check environment variables are set correctly
   - Verify Supabase connection
   - Check logs for specific error messages

3. **Frontend Not Loading**:
   - Ensure frontend build completed successfully
   - Check that static files are being served
   - Verify the catch-all route is working

## Custom Domain

To add a custom domain:
1. Go to Settings → Domains in your Railway service
2. Add your custom domain
3. Update your DNS records as instructed

## Scaling

Railway allows easy scaling:
- Adjust replica count in service settings
- Configure memory/CPU limits
- Set up autoscaling rules

## Cost

- Railway offers $5 free credits per month
- After that, pay-as-you-go pricing
- This app should cost ~$5-10/month for light usage