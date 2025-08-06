#!/usr/bin/env python3
"""Quick script to fix common style issues."""

import os
import re
from pathlib import Path

def fix_file_style(file_path):
    """Fix common style issues in a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove trailing whitespace
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        fixed_lines.append(line)
    
    # Ensure file ends with newline
    content = '\n'.join(fixed_lines)
    if content and not content.endswith('\n'):
        content += '\n'
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed: {file_path}")

def main():
    """Fix style issues in services directory."""
    services_dir = Path('services')
    
    for py_file in services_dir.glob('*.py'):
        fix_file_style(py_file)

if __name__ == '__main__':
    main()
