# AMC Manager

A full-stack application for managing Amazon Marketing Cloud (AMC) instances with editable brand tags and campaign filtering.

## Features

- 🏢 **AMC Instance Management**: View and manage multiple AMC instances across different accounts
- 🏷️ **Editable Brand Tags**: Associate brands directly with instances for better organization
- 📊 **Campaign Filtering**: Automatically filter campaigns based on instance brand associations
- 🔍 **Brand Search**: Autocomplete search for existing brands or create new ones
- 🚀 **Ready for Deployment**: Configured for Railway.app deployment

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Python 3.11
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Railway.app

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/amc-manager.git
cd amc-manager
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Start the services:
```bash
./start_services.sh
```

4. Access the application:
- Frontend: http://localhost:5173
- API: http://localhost:8001

### Deployment to Railway

See [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) for detailed deployment instructions.

## Project Structure

```
├── amc_manager/          # Backend Python package
│   ├── api/             # API endpoints
│   ├── core/            # Core utilities
│   └── services/        # Business logic
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   └── services/    # API clients
├── database/            # Database migrations
└── scripts/             # Utility scripts
```

## Key Features

### Brand Tag Management

- Edit brands directly on instance detail pages
- Add/remove brands with visual feedback
- Search existing brands or create new ones
- Changes persist and affect campaign filtering

### Campaign Filtering

- Campaigns automatically filter based on instance brands
- Brand associations determine which campaigns appear
- Supports multiple brand tags per instance

## Development

### Backend Development

```bash
cd /root/amazon-helper
python -m venv venv
source venv/bin/activate
pip install -r requirements_supabase.txt
python main_supabase.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

Run migrations in Supabase SQL editor:
```sql
-- See database/supabase/migrations/
```

## Testing

```bash
# Test instance brands functionality
python scripts/test_instance_brands.py

# Test campaign import
python scripts/test_campaign_import_mock.py
```

## License

MIT