"""
Analyze Newman test results and identify failing endpoints.
"""
import json
from pathlib import Path
from collections import defaultdict

def analyze_newman_results(results_file: str):
    """Analyze Newman JSON results and categorize failures."""
    
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group results by status code
    status_groups = defaultdict(list)
    
    for execution in data['run']['executions']:
        request = execution['request']
        response = execution.get('response', {})
        
        name = execution['item']['name']
        method = request['method']
        
        # Handle different URL formats
        if isinstance(request.get('url'), dict):
            url = request['url'].get('raw', str(request['url']))
        else:
            url = str(request.get('url', 'Unknown URL'))
        
        status_code = response.get('code', 'No Response')

        
        status_groups[status_code].append({
            'name': name,
            'method': method,
            'url': url,
            'status': status_code,
            'response_time': response.get('responseTime', 0),
            'body': response.get('body', '')[:200] if response.get('body') else ''
        })
    
    # Print summary
    print("=" * 80)
    print("NEWMAN TEST RESULTS ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Requests: {len(data['run']['executions'])}")
    print(f"Total Failures: {data['run']['stats']['requests']['failed']}")
    print(f"Total Passed: {data['run']['stats']['requests']['total'] - data['run']['stats']['requests']['failed']}")
    
    # Print by status code
    for status_code in sorted(status_groups.keys(), key=lambda x: (isinstance(x, str), x)):
        endpoints = status_groups[status_code]
        print(f"\n{'=' * 80}")
        print(f"STATUS CODE: {status_code} ({len(endpoints)} endpoints)")
        print('=' * 80)
        
        for endpoint in endpoints:
            print(f"\n  ❌ {endpoint['method']} {endpoint['name']}")
            print(f"     URL: {endpoint['url']}")
            if endpoint['body']:
                print(f"     Response: {endpoint['body']}")
    
    # Identify common issues
    print(f"\n{'=' * 80}")
    print("COMMON ISSUES DETECTED")
    print('=' * 80)
    
    # Check for double /api/v1 in URLs
    double_api = []
    for e in data['run']['executions']:
        req_url = e['request'].get('url', {})
        if isinstance(req_url, dict):
            url_str = req_url.get('raw', str(req_url))
        else:
            url_str = str(req_url)
        if '/api/v1/api/v1' in url_str:
            double_api.append(e)
    
    if double_api:
        print(f"\n⚠️  DOUBLE /api/v1 PREFIX DETECTED ({len(double_api)} endpoints)")
        print("   This is likely a configuration issue in the collection.")
        for exec in double_api[:5]:  # Show first 5
            req_url = exec['request'].get('url', {})
            if isinstance(req_url, dict):
                url = req_url.get('raw', str(req_url))
            else:
                url = str(req_url)
            print(f"   - {url}")
    
    # Check for 401 Unauthorized
    unauthorized = status_groups.get(401, [])
    if unauthorized:
        print(f"\n⚠️  AUTHENTICATION FAILURES ({len(unauthorized)} endpoints)")
        print("   These endpoints require valid authentication.")
    
    # Check for 404 Not Found
    not_found = status_groups.get(404, [])
    if not_found:
        print(f"\n⚠️  NOT FOUND ERRORS ({len(not_found)} endpoints)")
        print("   These endpoints may not be implemented or have incorrect URLs.")
    
    # Check for 422 Validation errors
    validation_errors = status_groups.get(422, [])
    if validation_errors:
        print(f"\n⚠️  VALIDATION ERRORS ({len(validation_errors)} endpoints)")
        print("   These endpoints have invalid request data.")
    
    # Check for 500 errors
    server_errors = status_groups.get(500, [])
    if server_errors:
        print(f"\n⚠️  SERVER ERRORS ({len(server_errors)} endpoints)")
        print("   These endpoints have internal server errors.")
    
    print("\n" + "=" * 80)
    
    return status_groups

if __name__ == "__main__":
    results_file = Path("postman/newman-results.json")
    if results_file.exists():
        analyze_newman_results(results_file)
    else:
        print(f"❌ Results file not found: {results_file}")
