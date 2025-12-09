"""
Enhance Postman collection with authentication and environment variables.

This script adds bearer token authentication to all endpoints that require it
and creates a Postman environment file.
"""
import json
import sys
from pathlib import Path

def enhance_collection(collection_path: str, output_path: str):
    """Add bearer token auth to collection."""
    
    with open(collection_path, 'r', encoding='utf-8') as f:
        collection = json.load(f)
    
    # Add collection-level auth
    collection['auth'] = {
        'type': 'bearer',
        'bearer': [
            {
                'key': 'token',
                'value': '{{bearerToken}}',
                'type': 'string'
            }
        ]
    }
    
    # Add variables
    collection['variable'] = [
        {
            'key': 'baseUrl',
            'value': 'http://localhost:8000/api/v1',
            'type': 'string'
        },
        {
            'key': 'bearerToken',
            'value': '',
            'type': 'string'
        }
    ]
    
    # Save enhanced collection
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Enhanced collection saved: {output_path}")

def create_environment(output_path: str):
    """Create Postman environment file."""
    
    environment = {
        'name': 'PixCrawler Development',
        'values': [
            {
                'key': 'baseUrl',
                'value': 'http://localhost:8000/api/v1',
                'type': 'default',
                'enabled': True
            },
            {
                'key': 'bearerToken',
                'value': '',
                'type': 'secret',
                'enabled': True
            }
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(environment, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Environment file created: {output_path}")

if __name__ == "__main__":
    enhance_collection('postman_collection.json', 'postman_collection_enhanced.json')
    create_environment('postman_environment.json')
