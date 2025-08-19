#!/usr/bin/env python3
"""Verify that the schedule executor service imports are correct"""

import os
import sys

def check_file(filepath, filename):
    """Check if a file has the correct imports"""
    print(f"\nChecking {filename}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for old incorrect import
    if 'from ..core.supabase_client import get_supabase_client' in content:
        print(f"  ❌ ERROR: {filename} still has old import 'get_supabase_client'")
        print(f"     Line: {content.find('from ..core.supabase_client import get_supabase_client')}")
        return False
    
    # Check for correct import
    if 'from ..core.supabase_client import SupabaseManager' in content:
        print(f"  ✅ {filename} has correct import 'SupabaseManager'")
        
        # Also check for correct usage
        if 'SupabaseManager.get_client()' in content:
            print(f"  ✅ {filename} uses SupabaseManager.get_client() correctly")
        elif 'get_supabase_client()' in content:
            print(f"  ❌ ERROR: {filename} still calls get_supabase_client()")
            return False
        
        return True
    
    # Check if file imports supabase_client at all
    if 'supabase_client' not in content:
        print(f"  ℹ️  {filename} doesn't import from supabase_client")
        return True
    
    print(f"  ⚠️  WARNING: {filename} has unexpected supabase_client import pattern")
    return False

def main():
    """Check all relevant files"""
    base_dir = '/root/amazon-helper'
    
    files_to_check = [
        ('amc_manager/services/schedule_executor_service.py', 'schedule_executor_service.py'),
        ('amc_manager/api/supabase/schedule_endpoints.py', 'schedule_endpoints.py'),
        ('amc_manager/services/enhanced_schedule_service.py', 'enhanced_schedule_service.py'),
    ]
    
    all_good = True
    
    print("=" * 60)
    print("Verifying Supabase Client Import Fixes")
    print("=" * 60)
    
    for relative_path, filename in files_to_check:
        filepath = os.path.join(base_dir, relative_path)
        if os.path.exists(filepath):
            if not check_file(filepath, filename):
                all_good = False
        else:
            print(f"\n❌ ERROR: {filename} not found at {filepath}")
            all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("✅ ALL CHECKS PASSED - Imports are correct!")
        print("\nThe application should work once deployed with these changes.")
    else:
        print("❌ SOME CHECKS FAILED - Please review the errors above")
        sys.exit(1)
    print("=" * 60)

if __name__ == '__main__':
    main()