"""
Generate OpenAPI specification from FastAPI app.

This script starts the FastAPI application and exports the OpenAPI schema
to a JSON file for use with Postman, Swagger, or other API tools.

Usage:
    python scripts/generate_openapi.py
    python scripts/generate_openapi.py --output custom_openapi.json
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.main import app

def generate_openapi(output_file: str = "openapi.json"):
    """Generate OpenAPI schema and save to file."""
    
    # Get OpenAPI schema from FastAPI app
    openapi_schema = app.openapi()
    
    # Save to file
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"✅ OpenAPI schema generated: {output_path.absolute()}")
    print(f"   Title: {openapi_schema.get('info', {}).get('title')}")
    print(f"   Version: {openapi_schema.get('info', {}).get('version')}")
    print(f"   Endpoints: {len(openapi_schema.get('paths', {}))}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate OpenAPI schema")
    parser.add_argument(
        "--output",
        "-o",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    
    args = parser.parse_args()
    generate_openapi(args.output)
