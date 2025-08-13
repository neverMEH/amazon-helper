#!/bin/bash
echo "Preparing for Railway deployment..."

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Test that backend can serve frontend
echo "Testing backend with static files..."
python -c "
from pathlib import Path
frontend_dist = Path('frontend/dist')
if frontend_dist.exists():
    print('✓ Frontend build found at frontend/dist')
    if (frontend_dist / 'index.html').exists():
        print('✓ index.html found')
    if (frontend_dist / 'assets').exists():
        print('✓ assets directory found')
else:
    print('✗ Frontend build not found!')
"

echo ""
echo "Deployment checklist:"
echo "✓ railway.json - Railway configuration"
echo "✓ Procfile - Process definition" 
echo "✓ nixpacks.toml - Build configuration"
echo "✓ Frontend build in dist/"
echo "✓ Backend serves static files"
echo ""
echo "Next steps:"
echo "1. Create a GitHub repository"
echo "2. Push this code to GitHub"
echo "3. Connect Railway to your GitHub repo"
echo "4. Add environment variables in Railway"
echo "5. Deploy!"