#!/usr/bin/env python3
"""
OpenAPI Specification Validator

This script validates the OpenAPI specification against the requirements:
1. Check for schema errors and warnings
2. Verify all required fields are present
3. Ensure all endpoints have proper request/response definitions
4. Confirm all examples use ISO 8601 timestamps and UUID v4 format
"""

import json
import re
import sys
from typing import Any, Dict, List, Tuple

# UUID v4 pattern
UUID_V4_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# ISO 8601 timestamp pattern (with optional milliseconds)
ISO_8601_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$'
)

class OpenAPIValidator:
    def __init__(self, spec_path: str):
        self.spec_path = spec_path
        self.spec = None
        self.errors = []
        self.warnings = []
        
    def load_spec(self) -> bool:
        """Load the OpenAPI specification from file."""
        try:
            with open(self.spec_path, 'r', encoding='utf-8') as f:
                self.spec = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
        except FileNotFoundError:
            self.errors.append(f"File not found: {self.spec_path}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading spec: {e}")
            return False
    
    def validate_structure(self) -> None:
        """Validate the basic OpenAPI structure."""
        # Check required top-level fields
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in self.spec:
                self.errors.append(f"Missing required top-level field: {field}")
        
        # Check OpenAPI version
        if 'openapi' in self.spec:
            version = self.spec['openapi']
            if not version.startswith('3.0'):
                self.warnings.append(f"OpenAPI version {version} may not be fully compatible with Prism")
        
        # Check info section
        if 'info' in self.spec:
            info = self.spec['info']
            required_info_fields = ['title', 'version']
            for field in required_info_fields:
                if field not in info:
                    self.errors.append(f"Missing required info field: {field}")
    
    def validate_endpoints(self) -> None:
        """Validate all endpoint definitions."""
        if 'paths' not in self.spec:
            return
        
        paths = self.spec['paths']
        endpoint_count = 0
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.lower() in ['get', 'post', 'put', 'patch', 'delete']:
                    endpoint_count += 1
                    self._validate_operation(path, method, operation)
        
        print(f"✓ Found {endpoint_count} endpoints")
        
        # Check if we have the expected 27 endpoints
        expected_endpoints = 27
        if endpoint_count != expected_endpoints:
            self.warnings.append(
                f"Expected {expected_endpoints} endpoints, found {endpoint_count}"
            )
    
    def _validate_operation(self, path: str, method: str, operation: Dict[str, Any]) -> None:
        """Validate a single operation."""
        endpoint_id = f"{method.upper()} {path}"
        
        # Check for required operation fields
        if 'responses' not in operation:
            self.errors.append(f"{endpoint_id}: Missing 'responses' field")
            return
        
        # Check for success response (200 or 201)
        responses = operation['responses']
        has_success = any(code in responses for code in ['200', '201'])
        if not has_success:
            self.errors.append(f"{endpoint_id}: Missing success response (200 or 201)")
        
        # Validate response schemas and examples
        for status_code, response in responses.items():
            if 'content' in response:
                for content_type, content in response['content'].items():
                    if content_type == 'application/json':
                        # Check for schema
                        if 'schema' not in content:
                            self.warnings.append(
                                f"{endpoint_id} [{status_code}]: Missing schema"
                            )
                        
                        # Check for example
                        if 'example' not in content:
                            self.warnings.append(
                                f"{endpoint_id} [{status_code}]: Missing example"
                            )
                        else:
                            # Validate example data
                            self._validate_example(
                                content['example'],
                                f"{endpoint_id} [{status_code}]"
                            )
        
        # Validate request body for POST/PUT/PATCH
        if method.upper() in ['POST', 'PUT', 'PATCH']:
            if 'requestBody' in operation:
                request_body = operation['requestBody']
                if 'content' in request_body:
                    for content_type, content in request_body['content'].items():
                        if content_type == 'application/json':
                            if 'schema' not in content:
                                self.warnings.append(
                                    f"{endpoint_id}: Request body missing schema"
                                )
                            if 'example' not in content:
                                self.warnings.append(
                                    f"{endpoint_id}: Request body missing example"
                                )
                            else:
                                self._validate_example(
                                    content['example'],
                                    f"{endpoint_id} [request]"
                                )
    
    def _validate_example(self, data: Any, context: str) -> None:
        """Recursively validate example data for UUIDs and timestamps."""
        if isinstance(data, dict):
            for key, value in data.items():
                # Check for UUID fields (but exclude fields that are clearly not UUIDs)
                # Only check fields that end with _id or are exactly 'id' or contain 'uuid'
                is_uuid_field = (
                    key.lower().endswith('_id') or 
                    key.lower() == 'id' or 
                    'uuid' in key.lower()
                )
                # Exclude fields that are clearly not UUIDs
                exclude_patterns = ['order_id', 'task_id', 'payment_token', 'level', 'key']
                is_excluded = any(pattern in key.lower() for pattern in exclude_patterns)
                
                if is_uuid_field and not is_excluded:
                    if isinstance(value, str) and value:
                        if not UUID_V4_PATTERN.match(value):
                            self.errors.append(
                                f"{context}: Invalid UUID v4 format in field '{key}': {value}"
                            )
                
                # Check for timestamp fields (fields ending with _at or containing timestamp)
                is_timestamp_field = (
                    key.lower().endswith('_at') or 
                    'timestamp' in key.lower()
                )
                # Exclude date-only fields and non-timestamp fields
                exclude_ts_patterns = ['date', 'level', 'order']
                is_ts_excluded = any(pattern in key.lower() for pattern in exclude_ts_patterns) and not key.lower().endswith('_at')
                
                if is_timestamp_field and not is_ts_excluded:
                    if isinstance(value, str) and value:
                        # Skip date-only fields (YYYY-MM-DD)
                        if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                            continue
                        if not ISO_8601_PATTERN.match(value):
                            self.errors.append(
                                f"{context}: Invalid ISO 8601 timestamp in field '{key}': {value}"
                            )
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self._validate_example(value, context)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._validate_example(item, context)
    
    def validate_schemas(self) -> None:
        """Validate component schemas."""
        if 'components' not in self.spec:
            self.warnings.append("No 'components' section found")
            return
        
        if 'schemas' not in self.spec['components']:
            self.warnings.append("No 'schemas' in components")
            return
        
        schemas = self.spec['components']['schemas']
        print(f"✓ Found {len(schemas)} component schemas")
        
        # Check for common schemas
        expected_schemas = ['UUID', 'Timestamp', 'PaginationMeta']
        for schema_name in expected_schemas:
            if schema_name not in schemas:
                self.warnings.append(f"Missing recommended schema: {schema_name}")
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations."""
        print("Validating OpenAPI specification...")
        print(f"File: {self.spec_path}\n")
        
        if not self.load_spec():
            return False, self.errors, self.warnings
        
        print("✓ Valid JSON format")
        
        self.validate_structure()
        self.validate_schemas()
        self.validate_endpoints()
        
        return len(self.errors) == 0, self.errors, self.warnings


def main():
    import os
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(script_dir, 'openapi.json')
    
    validator = OpenAPIValidator(spec_path)
    success, errors, warnings = validator.validate()
    
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")
    
    if success and not warnings:
        print("\n✅ All validations passed!")
        print("\nThe OpenAPI specification is valid and ready for use with Prism.")
        return 0
    elif success:
        print("\n✅ Validation passed with warnings")
        print("\nThe specification is valid but has some recommendations.")
        return 0
    else:
        print("\n❌ Validation failed")
        print("\nPlease fix the errors before using the specification.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
