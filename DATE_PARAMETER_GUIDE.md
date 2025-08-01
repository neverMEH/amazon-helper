# Date Parameter Editor Guide

## Overview
The workflow execution modal now includes an enhanced parameter editor with date range presets and improved input controls.

## Features

### 1. Date Range Presets
Click the "Select date range" dropdown to choose from common presets:
- **Last 7 days** - Previous 7 days from today
- **Last 14 days** - Previous 2 weeks
- **Last 30 days** - Previous month
- **Last 60 days** - Previous 2 months
- **Last 90 days** - Previous quarter
- **Last 180 days** - Previous 6 months
- **Last 365 days** - Previous year
- **Month to date** - From the 1st of current month to today
- **Year to date** - From January 1st to today
- **Custom range** - Manually set dates

### 2. Smart Date Inputs
- **Date parameters** (`start_date`, `end_date`) show a date picker
- **Number parameters** (`lookback_days`) show a numeric input with min/max validation
- **Array parameters** accept comma-separated values
- **Text parameters** show standard text inputs

### 3. Toggle Between Editors
- **Simple Editor** (default): User-friendly form with date pickers and dropdowns
- **Advanced Editor**: Raw JSON editor for power users (Monaco Editor)
- Toggle between them using the "Advanced Editor" button

## How It Works

### Automatic Date Calculation
When you select a preset like "Last 30 days":
1. The system calculates `start_date` as 30 days ago
2. Sets `end_date` as today
3. Updates `lookback_days` to 30 (if the parameter exists)

### Example Usage
1. Open workflow execution modal
2. Click "Select date range" dropdown
3. Choose "Last 30 days"
4. The parameters automatically update:
   ```json
   {
     "start_date": "2024-12-02",
     "end_date": "2025-01-01",
     "lookback_days": 30,
     "min_path_frequency": 10
   }
   ```

### Custom Parameters
- Click "Add Parameter" to add custom parameters
- Each parameter shows its name in a readable format
- Required parameters are marked with a red asterisk (*)

## Benefits
1. **No manual date formatting** - Prevents errors from incorrect date formats
2. **Quick selections** - Common ranges in one click
3. **Consistency** - All dates use YYYY-MM-DD format
4. **Flexibility** - Switch to JSON editor for complex configurations
5. **Validation** - Input validation based on parameter schema

## Technical Details
- Date format: ISO 8601 (YYYY-MM-DD)
- Lookback days are inclusive (Last 7 days includes today)
- Month/Year to date calculations use current system date
- All dates are calculated in the user's browser timezone