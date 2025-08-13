#!/usr/bin/env python3
"""
Automatic CLAUDE.md Documentation Updater
==========================================
This script analyzes the repository for changes and automatically updates the CLAUDE.md file
with comprehensive documentation of new features, fixes, and architectural changes.

Usage:
    python scripts/update_claude_md.py [--days=30] [--verbose] [--dry-run]
    
Options:
    --days: Number of days to look back for changes (default: 30)
    --verbose: Show detailed analysis output
    --dry-run: Show what would be updated without making changes
"""

import os
import sys
import re
import json
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import ast

class RepoAnalyzer:
    """Analyzes repository for changes and generates documentation updates."""
    
    def __init__(self, repo_path: str = ".", days_back: int = 30, verbose: bool = False):
        self.repo_path = Path(repo_path)
        self.days_back = days_back
        self.verbose = verbose
        self.since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        # Categories for organizing changes
        self.change_categories = {
            'features': [],
            'fixes': [],
            'components': [],
            'api_endpoints': [],
            'services': [],
            'database': [],
            'dependencies': [],
            'configuration': [],
            'documentation': [],
            'performance': [],
            'security': [],
            'refactoring': []
        }
        
        # File patterns to analyze
        self.patterns = {
            'frontend_components': 'frontend/src/components/**/*.tsx',
            'frontend_pages': 'frontend/src/pages/**/*.tsx',
            'frontend_services': 'frontend/src/services/**/*.ts',
            'frontend_hooks': 'frontend/src/hooks/**/*.ts',
            'frontend_utils': 'frontend/src/utils/**/*.ts',
            'backend_api': 'amc_manager/api/**/*.py',
            'backend_services': 'amc_manager/services/**/*.py',
            'backend_models': 'amc_manager/models/**/*.py',
            'database': 'database/**/*.sql',
            'scripts': 'scripts/**/*.py',
            'config': ['*.json', '*.yml', '*.yaml', '.env.example', 'Dockerfile'],
            'docs': 'docs/**/*.md'
        }
        
    def run_git_command(self, cmd: str) -> str:
        """Execute a git command and return output."""
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if self.verbose:
                print(f"Git command failed: {cmd}\nError: {e.stderr}")
            return ""
    
    def get_recent_commits(self) -> List[Dict]:
        """Get all commits since the specified date."""
        cmd = f"git log --since={self.since_date} --pretty=format:%H|%ai|%an|%s --no-merges"
        output = self.run_git_command(cmd)
        
        commits = []
        for line in output.split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 4:
                    commits.append({
                        'hash': parts[0],
                        'date': parts[1].split()[0],
                        'author': parts[2],
                        'message': '|'.join(parts[3:])  # Handle pipes in commit message
                    })
        
        if self.verbose:
            print(f"Found {len(commits)} commits since {self.since_date}")
        
        return commits
    
    def analyze_commit_changes(self, commit_hash: str) -> Dict:
        """Analyze changes in a specific commit."""
        # Get changed files
        cmd = f"git diff-tree --no-commit-id --name-status -r {commit_hash}"
        output = self.run_git_command(cmd)
        
        changes = {
            'added_files': [],
            'modified_files': [],
            'deleted_files': [],
            'file_types': defaultdict(int)
        }
        
        for line in output.split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    status, filepath = parts[0], parts[1]
                    
                    if status == 'A':
                        changes['added_files'].append(filepath)
                    elif status == 'M':
                        changes['modified_files'].append(filepath)
                    elif status == 'D':
                        changes['deleted_files'].append(filepath)
                    
                    # Track file types
                    ext = Path(filepath).suffix
                    if ext:
                        changes['file_types'][ext] += 1
        
        return changes
    
    def extract_new_components(self) -> List[Dict]:
        """Find all React components created or modified recently."""
        components = []
        
        # Get all component files modified recently
        cmd = f"git diff --name-only --since={self.since_date} -- 'frontend/src/components/**/*.tsx'"
        output = self.run_git_command(cmd)
        
        for filepath in output.split('\n'):
            if filepath:
                # Check if file exists (not deleted)
                full_path = self.repo_path / filepath
                if full_path.exists():
                    component_info = self.analyze_react_component(full_path)
                    if component_info:
                        components.append(component_info)
        
        return components
    
    def analyze_react_component(self, filepath: Path) -> Optional[Dict]:
        """Analyze a React component file for documentation."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Extract component name
            component_match = re.search(r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)', content)
            if not component_match:
                return None
            
            component_name = component_match.group(1)
            
            # Extract props interface
            props_match = re.search(r'interface\s+\w*Props\s*\{([^}]+)\}', content, re.DOTALL)
            props = []
            if props_match:
                props_content = props_match.group(1)
                prop_lines = re.findall(r'(\w+)\s*\??\s*:\s*([^;]+)', props_content)
                props = [{'name': p[0], 'type': p[1].strip()} for p in prop_lines]
            
            # Extract hooks used
            hooks = list(set(re.findall(r'use[A-Z]\w+', content)))
            
            # Extract imported components
            imports = re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content)
            
            # Check for new features
            features = []
            if 'useState' in content and 'useEffect' in content:
                features.append('Stateful with side effects')
            if 'useQuery' in content or 'useMutation' in content:
                features.append('API integration')
            if 'toast' in content:
                features.append('User notifications')
            if 'Modal' in content or 'Dialog' in content:
                features.append('Modal/Dialog functionality')
            
            return {
                'name': component_name,
                'path': str(filepath.relative_to(self.repo_path)),
                'props': props,
                'hooks': hooks,
                'features': features,
                'imports': imports[:5]  # Limit to first 5 imports
            }
        except Exception as e:
            if self.verbose:
                print(f"Error analyzing component {filepath}: {e}")
            return None
    
    def extract_new_api_endpoints(self) -> List[Dict]:
        """Find all API endpoints added or modified recently."""
        endpoints = []
        
        # Get all API files modified recently
        cmd = f"git diff --name-only --since={self.since_date} -- 'amc_manager/api/**/*.py'"
        output = self.run_git_command(cmd)
        
        for filepath in output.split('\n'):
            if filepath:
                full_path = self.repo_path / filepath
                if full_path.exists():
                    file_endpoints = self.analyze_fastapi_endpoints(full_path)
                    endpoints.extend(file_endpoints)
        
        return endpoints
    
    def analyze_fastapi_endpoints(self, filepath: Path) -> List[Dict]:
        """Extract FastAPI endpoints from a Python file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            endpoints = []
            
            # Find all route decorators
            route_pattern = r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            matches = re.findall(route_pattern, content)
            
            for method, path in matches:
                # Try to find the function name and docstring
                func_pattern = rf'@(?:router|app)\.{method}\s*\([^)]*\)\s*(?:.*\n)*?(?:async\s+)?def\s+(\w+)'
                func_match = re.search(func_pattern, content)
                
                endpoint_info = {
                    'method': method.upper(),
                    'path': path,
                    'file': str(filepath.relative_to(self.repo_path)),
                    'function': func_match.group(1) if func_match else 'unknown'
                }
                
                # Try to extract docstring
                if func_match:
                    doc_pattern = rf'def\s+{func_match.group(1)}[^:]*:\s*"""([^"]+)"""'
                    doc_match = re.search(doc_pattern, content, re.DOTALL)
                    if doc_match:
                        endpoint_info['description'] = doc_match.group(1).strip().split('\n')[0]
                
                endpoints.append(endpoint_info)
            
            return endpoints
        except Exception as e:
            if self.verbose:
                print(f"Error analyzing API file {filepath}: {e}")
            return []
    
    def extract_new_services(self) -> List[Dict]:
        """Find all backend services added or modified recently."""
        services = []
        
        cmd = f"git diff --name-only --since={self.since_date} -- 'amc_manager/services/**/*.py'"
        output = self.run_git_command(cmd)
        
        for filepath in output.split('\n'):
            if filepath:
                full_path = self.repo_path / filepath
                if full_path.exists():
                    service_info = self.analyze_python_service(full_path)
                    if service_info:
                        services.append(service_info)
        
        return services
    
    def analyze_python_service(self, filepath: Path) -> Optional[Dict]:
        """Analyze a Python service file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Extract class definitions
            classes = re.findall(r'class\s+(\w+)(?:\([^)]*\))?:', content)
            
            # Extract main functions
            functions = re.findall(r'^(?:async\s+)?def\s+(\w+)\s*\([^)]*\):', content, re.MULTILINE)
            public_functions = [f for f in functions if not f.startswith('_')]
            
            # Check for important patterns
            patterns = {
                'uses_supabase': 'supabase' in content.lower(),
                'uses_async': 'async def' in content,
                'has_error_handling': 'try:' in content and 'except' in content,
                'has_logging': 'logger' in content or 'logging' in content,
                'is_background_service': 'Thread' in content or 'threading' in content,
                'uses_polling': 'poll' in content.lower() or 'interval' in content.lower()
            }
            
            return {
                'name': filepath.stem,
                'path': str(filepath.relative_to(self.repo_path)),
                'classes': classes,
                'public_functions': public_functions[:10],  # Limit to first 10
                'patterns': {k: v for k, v in patterns.items() if v}
            }
        except Exception as e:
            if self.verbose:
                print(f"Error analyzing service {filepath}: {e}")
            return None
    
    def extract_database_changes(self) -> List[Dict]:
        """Find all database migrations and schema changes."""
        changes = []
        
        # Check for SQL files
        cmd = f"git diff --name-only --since={self.since_date} -- '*.sql'"
        output = self.run_git_command(cmd)
        
        for filepath in output.split('\n'):
            if filepath:
                full_path = self.repo_path / filepath
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    
                    # Extract table operations
                    tables_created = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', content, re.IGNORECASE)
                    tables_altered = re.findall(r'ALTER\s+TABLE\s+(\w+)', content, re.IGNORECASE)
                    indexes_created = re.findall(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', content, re.IGNORECASE)
                    
                    if tables_created or tables_altered or indexes_created:
                        changes.append({
                            'file': str(filepath),
                            'tables_created': list(set(tables_created)),
                            'tables_altered': list(set(tables_altered)),
                            'indexes_created': list(set(indexes_created))
                        })
        
        return changes
    
    def extract_dependency_changes(self) -> Dict:
        """Check for changes in dependencies."""
        deps = {'frontend': {}, 'backend': {}}
        
        # Check package.json changes
        cmd = f"git diff --since={self.since_date} -- '**/package.json'"
        output = self.run_git_command(cmd)
        
        if output:
            # Extract added dependencies
            added_deps = re.findall(r'\+\s*"([^"]+)":\s*"([^"]+)"', output)
            removed_deps = re.findall(r'-\s*"([^"]+)":\s*"([^"]+)"', output)
            
            deps['frontend']['added'] = added_deps
            deps['frontend']['removed'] = removed_deps
        
        # Check requirements.txt changes
        cmd = f"git diff --since={self.since_date} -- 'requirements.txt'"
        output = self.run_git_command(cmd)
        
        if output:
            added_reqs = re.findall(r'\+([a-zA-Z0-9\-_]+)', output)
            removed_reqs = re.findall(r'-([a-zA-Z0-9\-_]+)', output)
            
            deps['backend']['added'] = added_reqs
            deps['backend']['removed'] = removed_reqs
        
        return deps
    
    def categorize_commits(self, commits: List[Dict]) -> None:
        """Categorize commits by type based on commit messages."""
        for commit in commits:
            msg = commit['message'].lower()
            
            # Categorize based on conventional commit format or keywords
            if msg.startswith('feat:') or msg.startswith('feature:') or 'add' in msg or 'implement' in msg:
                self.change_categories['features'].append(commit)
            elif msg.startswith('fix:') or 'fix' in msg or 'bug' in msg or 'error' in msg:
                self.change_categories['fixes'].append(commit)
            elif msg.startswith('docs:') or 'document' in msg or 'readme' in msg:
                self.change_categories['documentation'].append(commit)
            elif msg.startswith('perf:') or 'performance' in msg or 'optimize' in msg:
                self.change_categories['performance'].append(commit)
            elif msg.startswith('security:') or 'security' in msg or 'auth' in msg or 'token' in msg:
                self.change_categories['security'].append(commit)
            elif msg.startswith('refactor:') or 'refactor' in msg or 'restructure' in msg:
                self.change_categories['refactoring'].append(commit)
            elif 'component' in msg or 'ui' in msg or 'frontend' in msg:
                self.change_categories['components'].append(commit)
            elif 'api' in msg or 'endpoint' in msg:
                self.change_categories['api_endpoints'].append(commit)
            elif 'service' in msg or 'backend' in msg:
                self.change_categories['services'].append(commit)
            elif 'database' in msg or 'migration' in msg or 'schema' in msg:
                self.change_categories['database'].append(commit)
            elif 'config' in msg or 'env' in msg or 'docker' in msg:
                self.change_categories['configuration'].append(commit)
    
    def generate_claude_md_updates(self) -> str:
        """Generate the updated content for CLAUDE.md."""
        updates = []
        
        # Get all recent changes
        commits = self.get_recent_commits()
        if not commits:
            return "No recent changes found."
        
        self.categorize_commits(commits)
        
        # Extract detailed information
        new_components = self.extract_new_components()
        new_endpoints = self.extract_new_api_endpoints()
        new_services = self.extract_new_services()
        db_changes = self.extract_database_changes()
        dep_changes = self.extract_dependency_changes()
        
        # Build the updates section
        today = datetime.now().strftime("%Y-%m-%d")
        updates.append(f"\n#### {today} (Auto-Generated Update)")
        
        # Features
        if self.change_categories['features']:
            updates.append("\n**New Features:**")
            for commit in self.change_categories['features'][:5]:  # Limit to top 5
                updates.append(f"- {commit['message']}")
                # Add details about what changed
                changes = self.analyze_commit_changes(commit['hash'])
                if changes['added_files']:
                    updates.append(f"  - New files: {', '.join(changes['added_files'][:3])}")
        
        # Components
        if new_components:
            updates.append("\n**New/Updated Components:**")
            for comp in new_components[:10]:  # Limit to top 10
                updates.append(f"- `{comp['name']}` ({comp['path']})")
                if comp['features']:
                    updates.append(f"  - Features: {', '.join(comp['features'])}")
                if comp['props']:
                    props_str = ', '.join([p['name'] for p in comp['props'][:5]])
                    updates.append(f"  - Props: {props_str}")
        
        # API Endpoints
        if new_endpoints:
            updates.append("\n**New/Updated API Endpoints:**")
            for endpoint in new_endpoints[:10]:
                updates.append(f"- `{endpoint['method']} {endpoint['path']}` ({endpoint['function']})")
                if 'description' in endpoint:
                    updates.append(f"  - {endpoint['description']}")
        
        # Services
        if new_services:
            updates.append("\n**New/Updated Services:**")
            for service in new_services[:10]:
                updates.append(f"- `{service['name']}` ({service['path']})")
                if service['classes']:
                    updates.append(f"  - Classes: {', '.join(service['classes'])}")
                if service['patterns']:
                    patterns_str = ', '.join(service['patterns'].keys())
                    updates.append(f"  - Patterns: {patterns_str}")
        
        # Database Changes
        if db_changes:
            updates.append("\n**Database Changes:**")
            for change in db_changes:
                updates.append(f"- {change['file']}")
                if change['tables_created']:
                    updates.append(f"  - New tables: {', '.join(change['tables_created'])}")
                if change['tables_altered']:
                    updates.append(f"  - Modified tables: {', '.join(change['tables_altered'])}")
                if change['indexes_created']:
                    updates.append(f"  - New indexes: {', '.join(change['indexes_created'])}")
        
        # Dependency Changes
        if dep_changes['frontend'].get('added') or dep_changes['backend'].get('added'):
            updates.append("\n**Dependency Updates:**")
            if dep_changes['frontend'].get('added'):
                updates.append("- Frontend additions:")
                for dep, version in dep_changes['frontend']['added'][:5]:
                    updates.append(f"  - {dep}: {version}")
            if dep_changes['backend'].get('added'):
                updates.append("- Backend additions:")
                for dep in dep_changes['backend']['added'][:5]:
                    updates.append(f"  - {dep}")
        
        # Bug Fixes
        if self.change_categories['fixes']:
            updates.append("\n**Bug Fixes:**")
            for commit in self.change_categories['fixes'][:5]:
                updates.append(f"- {commit['message']}")
        
        # Performance Improvements
        if self.change_categories['performance']:
            updates.append("\n**Performance Improvements:**")
            for commit in self.change_categories['performance'][:3]:
                updates.append(f"- {commit['message']}")
        
        # Security Updates
        if self.change_categories['security']:
            updates.append("\n**Security Updates:**")
            for commit in self.change_categories['security'][:3]:
                updates.append(f"- {commit['message']}")
        
        return '\n'.join(updates)
    
    def update_claude_md(self, dry_run: bool = False) -> None:
        """Update the CLAUDE.md file with new documentation."""
        claude_md_path = self.repo_path / "CLAUDE.md"
        
        if not claude_md_path.exists():
            print("CLAUDE.md not found!")
            return
        
        # Read current content
        current_content = claude_md_path.read_text(encoding='utf-8')
        
        # Generate updates
        updates = self.generate_claude_md_updates()
        
        if not updates or updates == "No recent changes found.":
            print("No updates needed for CLAUDE.md")
            return
        
        # Find the right place to insert updates
        # Look for "### Recent Fixes and Enhancements" section
        section_pattern = r'(### Recent Fixes and Enhancements\s*\n)'
        match = re.search(section_pattern, current_content)
        
        if match:
            # Insert new updates right after the section header
            insert_pos = match.end()
            updated_content = (
                current_content[:insert_pos] +
                updates + '\n' +
                current_content[insert_pos:]
            )
        else:
            # If section doesn't exist, add it before the last section
            updated_content = current_content + "\n\n### Recent Fixes and Enhancements\n" + updates
        
        if dry_run:
            print("=== DRY RUN - Changes that would be made ===")
            print(updates)
            print("============================================")
        else:
            # Write updated content
            claude_md_path.write_text(updated_content, encoding='utf-8')
            print(f"✅ Successfully updated CLAUDE.md with {len(updates.splitlines())} lines of documentation")
            
            # Show summary
            print("\nSummary of updates added:")
            for line in updates.split('\n')[:20]:  # Show first 20 lines
                if line.startswith('**') or line.startswith('####'):
                    print(f"  {line}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Automatically update CLAUDE.md with repository changes'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to look back for changes (default: 30)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed analysis output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    
    args = parser.parse_args()
    
    print(f"🔍 Analyzing repository changes from the last {args.days} days...")
    
    analyzer = RepoAnalyzer(days_back=args.days, verbose=args.verbose)
    analyzer.update_claude_md(dry_run=args.dry_run)
    
    if not args.dry_run:
        print("\n💡 Tip: Run 'git diff CLAUDE.md' to review the changes")
        print("   Then commit with: git add CLAUDE.md && git commit -m 'docs: Auto-update CLAUDE.md with recent changes'")

if __name__ == "__main__":
    main()