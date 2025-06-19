#!/usr/bin/env python3

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""
NS8 Agent Method Compatibility Check
This script validates that all agent method calls in the codebase are NS8-compliant
"""

import os
import sys
import re
import glob
from pathlib import Path

def check_python_file(filepath):
    """Check a Python file for deprecated agent method calls"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        # Check for deprecated agent method patterns
        deprecated_patterns = [
            (r'agent\.log_info\s*\(', 'agent.log_info() is deprecated - use print(agent.SD_INFO + message, file=sys.stderr)'),
            (r'agent\.log_warning\s*\(', 'agent.log_warning() is deprecated - use print(agent.SD_WARNING + message, file=sys.stderr)'),
            (r'agent\.log_error\s*\(', 'agent.log_error() is deprecated - use print(agent.SD_ERR + message, file=sys.stderr)'),
            (r'agent\.dump_env\s*\(', 'agent.dump_env() is deprecated and no longer needed'),
            (r'agent\.list_service_providers\s*\(', 'agent.list_service_providers() is deprecated - use Redis key scanning'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, message in deprecated_patterns:
                if re.search(pattern, line):
                    issues.append({
                        'file': filepath,
                        'line': line_num,
                        'content': line.strip(),
                        'issue': message
                    })
    
    except Exception as e:
        issues.append({
            'file': filepath,
            'line': 0,
            'content': '',
            'issue': f'Error reading file: {e}'
        })
    
    return issues

def check_all_files():
    """Check all Python files in the project"""
    all_issues = []
    
    # Find all Python files in the imageroot directory
    python_files = []
    for root, dirs, files in os.walk('imageroot'):
        for file in files:
            if file.endswith('.py') or (os.path.isfile(os.path.join(root, file)) and 
                                       not file.endswith('.json')):
                # Check if it's a Python file by checking shebang
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        first_line = f.readline()
                        if 'python' in first_line or file.endswith('.py'):
                            python_files.append(filepath)
                except:
                    pass
    
    print(f"Checking {len(python_files)} Python files for deprecated agent method calls...")
    
    for filepath in python_files:
        issues = check_python_file(filepath)
        all_issues.extend(issues)
    
    return all_issues

def main():
    """Main function"""
    print("NS8 Agent Method Compatibility Check")
    print("=" * 50)
    
    issues = check_all_files()
    
    if not issues:
        print("✅ All files are NS8-compliant! No deprecated agent methods found.")
        return 0
    
    print(f"❌ Found {len(issues)} compatibility issues:")
    print()
    
    for issue in issues:
        print(f"📁 File: {issue['file']}")
        print(f"📍 Line {issue['line']}: {issue['content']}")
        print(f"⚠️  Issue: {issue['issue']}")
        print("-" * 60)
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
