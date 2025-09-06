# Data Collections Feature - Setup Guide

## Implementation Status ✅

The Data Collections feature is **fully implemented** across backend and frontend. All components are in place and functional.

## What's Been Implemented

### Backend
- ✅ Database schema (7 tables) - Migration script ready at `scripts/migrations/003_create_reporting_tables.sql`
- ✅ Service layer (`ReportingDatabaseService`, `HistoricalCollectionService`, etc.)
- ✅ API endpoints at `/api/data-collections/*`
- ✅ Background executor service for async processing
- ✅ Integration with main application lifecycle

### Frontend
- ✅ Data Collections UI at `/data-collections`
- ✅ Collection list view with real-time progress
- ✅ Searchable workflow and instance selectors
- ✅ Collection management (pause, resume, cancel, retry)
- ✅ Week-by-week progress tracking

## Setup Requirements

### 1. Apply Database Migration

The feature requires database tables. Run this migration in your Supabase SQL editor:

```sql
-- Run the migration script:
-- Located at: scripts/migrations/003_create_reporting_tables.sql
```

This creates:
- `report_data_collections` - Main collection records
- `report_data_weeks` - Week-by-week execution tracking
- `report_data_aggregates` - Pre-computed metrics
- `dashboards` - Dashboard configurations
- `dashboard_widgets` - Widget definitions
- `ai_insights` - AI-generated insights
- `dashboard_shares` - Sharing permissions

### 2. Environment Configuration

Ensure your `.env` file has proper database credentials:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

For AI insights (optional):
```bash
export ANTHROPIC_API_KEY="your-key"  # Set as environment variable
export OPENAI_API_KEY="your-key"     # Alternative AI provider
```

### 3. Service Dependencies

The feature depends on:
- Working AMC instance configurations
- At least one workflow created
- Valid user authentication tokens

## How to Use

1. **Navigate to Data Collections**
   - Click "Data Collections" in the sidebar
   - Or go to `/data-collections` directly

2. **Start a Collection**
   - Click "Start Collection"
   - Search and select a workflow
   - Search and select an AMC instance
   - Choose number of weeks (1-52)
   - Select collection type (backfill or weekly update)

3. **Monitor Progress**
   - View real-time progress bars
   - Click any collection to see week-by-week details
   - Use pause/resume controls as needed
   - Retry failed weeks individually

## API Endpoints

```http
# Create collection
POST /api/data-collections/
{
  "workflow_id": "uuid",
  "instance_id": "uuid",
  "target_weeks": 52,
  "collection_type": "backfill"
}

# List collections
GET /api/data-collections/

# Get progress
GET /api/data-collections/{collection_id}

# Control operations
POST /api/data-collections/{collection_id}/pause
POST /api/data-collections/{collection_id}/resume
POST /api/data-collections/{collection_id}/retry-failed
DELETE /api/data-collections/{collection_id}
```

## Troubleshooting

### "404 Not Found" Errors
✅ **Fixed** - Was caused by double `/api/api` prefix, now resolved

### No Instances/Workflows Showing
- Ensure you have created instances and workflows first
- Check that API calls to `/api/instances` and `/api/workflows` work
- Verify authentication is working

### Collections Not Starting
- Check if database tables exist (run migration)
- Verify background services are running
- Check server logs for specific errors

### Empty Instance Names
✅ **Fixed** - Added fallback to "Unnamed Instance" and proper field mapping

## Architecture Overview

```
Frontend (React)
    ↓
DataCollections.tsx → dataCollectionService.ts
    ↓
API Layer (/api/data-collections/)
    ↓
Backend Services:
- HistoricalCollectionService (manages collections)
- CollectionExecutorService (background processing)
- ReportingDatabaseService (database operations)
    ↓
Database (Supabase/PostgreSQL)
```

## Next Steps

After Phase 3 (Data Collections) is complete, the roadmap continues with:

- **Phase 4**: Basic Dashboard Visualization
- **Phase 5**: Dashboard Builder Interface
- **Phase 6**: Automated Weekly Updates
- **Phase 7**: AI-Powered Insights Frontend
- **Phase 8**: Export and Sharing

## Recent Fixes

1. **Routing Fix** (commit `e05ed88`)
   - Fixed double `/api/api` prefix issue
   - Routes now correctly resolve

2. **Selector Improvements** (commit `83e12e3`)
   - Added searchable workflow selector
   - Fixed instance selector with proper field mapping
   - Both support real-time search and metadata display

3. **TypeScript Fixes** (commits `a3c2f0c`, `16f21e7`)
   - Removed unused imports
   - Fixed method names
   - Build now passes successfully

## Summary

The Data Collections feature is **fully functional** once the database migration is applied. All code is implemented, tested, and ready for use. The feature provides comprehensive 52-week historical data backfill capabilities with a modern, searchable UI and robust background processing.