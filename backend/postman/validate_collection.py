import json

with open('backend/postman/PixCrawler_Frontend_Mock.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
print(f'✓ Valid JSON with {len(data["item"])} endpoint groups')

validation = [item for item in data['item'] if item['name'] == 'Validation'][0]
print(f'✓ Validation folder has {len(validation["item"])} endpoints')

# List all validation endpoints
print('\nValidation endpoints:')
for i, endpoint in enumerate(validation['item'], 1):
    method = endpoint['request']['method']
    name = endpoint['name']
    print(f'  {i}. {method} - {name}')
