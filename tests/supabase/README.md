# Supabase Integration Tests

This directory contains tests for the Supabase integration with Amazon AMC Manager.

## Test Files

### test_supabase_simple.py
Basic connection test to verify Supabase credentials and connectivity.

```bash
python tests/supabase/test_supabase_simple.py
```

### test_supabase_connection.py
Comprehensive connection test that verifies:
- Client initialization
- Database connectivity
- Table access
- RPC function availability

```bash
python tests/supabase/test_supabase_connection.py
```

### test_supabase_integration.py
Full integration test that demonstrates:
- Brand configuration creation
- Campaign mapping with ASINs
- ASIN-based search
- Workflow management
- Real-time subscription setup

```bash
python tests/supabase/test_supabase_integration.py
```

## Running Tests

### Prerequisites
1. Supabase tables must be created (run SQL scripts first)
2. Environment variables must be set in `.env`
3. Python dependencies installed: `pip install -r requirements.txt`

### Run All Tests
```bash
# From project root
python -m pytest tests/supabase/

# Or run individually
python tests/supabase/test_supabase_connection.py
```

## Test Data
Tests use mock data with:
- Test user ID: `00000000-0000-0000-0000-000000000000`
- Test brand: `TEST_BRAND`
- Test ASINs: `B001TEST`, `B002TEST`, `B003TEST`
- Test campaign ID: `12345`

## Troubleshooting

### Connection Errors
- Verify Supabase URL and keys in `.env`
- Check if Supabase project is active
- Ensure network connectivity

### Table Not Found
- Run database setup scripts in correct order
- Check Supabase dashboard for any SQL errors
- Verify tables exist in correct schema (public)

### Permission Errors
- Check RLS policies are applied
- Use service role key for testing
- Verify user authentication setup