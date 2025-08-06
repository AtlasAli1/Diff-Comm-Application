#!/usr/bin/env python3
"""Advanced script to fix remaining style issues."""

import re
from pathlib import Path

def fix_imports_and_continuations(file_path):
    """Fix unused imports and continuation line issues."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove unused imports for analytics_service.py
    if 'analytics_service.py' in str(file_path):
        # Remove unused imports
        content = re.sub(r'from typing import Dict, List, Any, Optional, Tuple\n', 
                        'from typing import Dict, List, Any\n', content)
        content = re.sub(r'from datetime import datetime, date, timedelta\n', 
                        '', content)
        content = re.sub(r'from plotly\.subplots import make_subplots\n', 
                        '', content)
        content = re.sub(r'from sklearn\.preprocessing import StandardScaler\n', 
                        '', content)
    
    # Remove unused imports for commission_service.py
    if 'commission_service.py' in str(file_path):
        content = re.sub(r'from datetime import datetime, date\n', '', content)
        content = re.sub(r'import pandas as pd\n', '', content)
    
    # Remove unused imports for data_service.py  
    if 'data_service.py' in str(file_path):
        content = re.sub(r'import numpy as np\n', '', content)
        content = re.sub(r'from decimal import Decimal\n', '', content)
        content = re.sub(r'from typing import Dict, List, Any, Optional, Tuple, Union\n',
                        'from typing import Dict, List, Any, Tuple\n', content)
        content = re.sub(r'from datetime import datetime, date\n',
                        'from datetime import datetime\n', content)
    
    # Fix line length issues
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if len(line) > 120:
            # Try to break long lines at logical points
            if 'logger.info(' in line and 'total commissions' in line:
                # Split the long logger line
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(f"{' ' * indent}logger.info(")
                fixed_lines.append(f"{' ' * (indent + 4)}f\"Commission summary: {{summary['employees_count']}} employees, \"")
                fixed_lines.append(f"{' ' * (indent + 4)}f\"${{summary['total_commissions']}} total commissions\"")
                fixed_lines.append(f"{' ' * indent})")
            elif 'quality_metrics[\'recommendations\']' in line:
                # Split the long recommendation line
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(f"{' ' * indent}quality_metrics['recommendations'].append(")
                fixed_lines.append(f"{' ' * (indent + 4)}\"Add technician assignments for work done commissions\"")
                fixed_lines.append(f"{' ' * indent})")
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Advanced fixes applied to: {file_path}")

def main():
    """Apply advanced style fixes."""
    services_dir = Path('services')
    
    for py_file in services_dir.glob('*.py'):
        if py_file.name != '__init__.py':
            fix_imports_and_continuations(py_file)

if __name__ == '__main__':
    main()
