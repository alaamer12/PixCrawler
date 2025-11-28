#!/usr/bin/env python
"""Script to fix parameter ordering in metrics.py - move service to the beginning"""
import re

# Read the file
with open('backend/api/v1/endpoints/metrics.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is a function definition line
    if line.strip().startswith('async def '):
        # Collect the entire function signature
        signature_lines = []
        j = i
        while j < len(lines):
            signature_lines.append(lines[j])
            if '->' in lines[j] or ')' in lines[j]:
                # Found the end of signature
                signature = ''.join(signature_lines)
                
                # Check if this signature has both current_user and service
                if 'current_user: dict = Depends(get_current_user)' in signature and 'service: MetricsServiceDep' in signature:
                    # Need to fix parameter order
                    # Parse parameters
                    params_start = signature.find('(') + 1
                    params_end = signature.rfind(')')
                    params_and_return = signature[params_end:]
                    params_section = signature[params_start:params_end]
                    
                    # Split into individual parameters (simple approach)
                    # We'll reconstruct by moving service to before current_user
                    fixed_signature = signature.replace(
                        ',\n    current_user: dict = Depends(get_current_user),\n    service: MetricsServiceDep',
                        ',\n    service: MetricsServiceDep,\n    current_user: dict = Depends(get_current_user)'
                    )
                    
                    # Output the fixed signature
                    output_lines.extend(fixed_signature.splitlines(keepends=True))
                else:
                    # Output as-is
                    output_lines.extend(signature_lines)
                
                i = j + 1
                break
            j += 1
        continue
    
    output_lines.append(line)
    i += 1

# Write back
with open('backend/api/v1/endpoints/metrics.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("Fixed parameter ordering issues in metrics.py")
