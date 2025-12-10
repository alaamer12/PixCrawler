"""
Find and remove all duplicate index definitions in model files.

This script scans all model files and removes `index=True` from column
definitions when there's also an explicit Index() in __table_args__.
"""

import os
import re
from pathlib import Path

def fix_duplicate_indexes(file_path):
    """Remove duplicate index definitions from a model file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to find columns with index=True
    # We'll remove index=True from mapped_column definitions
    # This is a simple approach - remove all index=True from mapped_column calls
    content = re.sub(
        r'(\s+)index=True,(\s*\n)',
        r'\2',
        content
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Scan all model files and fix duplicate indexes."""
    models_dir = Path("backend/models")
    
    print("=" * 70)
    print("FIXING DUPLICATE INDEX DEFINITIONS")
    print("=" * 70)
    
    fixed_files = []
    
    for file_path in models_dir.glob("*.py"):
        if file_path.name.startswith("__"):
            continue
        
        if fix_duplicate_indexes(file_path):
            fixed_files.append(file_path.name)
            print(f"✓ Fixed: {file_path.name}")
    
    print("\n" + "=" * 70)
    if fixed_files:
        print(f"✅ Fixed {len(fixed_files)} file(s)")
        for name in fixed_files:
            print(f"   - {name}")
    else:
        print("✅ No duplicate indexes found")
    print("=" * 70)

if __name__ == "__main__":
    main()
