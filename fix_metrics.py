#!/usr/bin/env python
"""Script to fix parameter ordering in metrics.py"""
import re

# Read the file
with open('backend/api/v1/endpoints/metrics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all instances where current_user with Depends comes before service
pattern1 = r'(\s+)current_user: dict = Depends\(get_current_user\),(\r?\n\s+)service: MetricsServiceDep'
replacement1 = r'\1service: MetricsServiceDep,\2current_user: dict = Depends(get_current_user)'

content = re.sub(pattern1, replacement1, content)

# Write back
with open('backend/api/v1/endpoints/metrics.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all parameter ordering issues in metrics.py")
