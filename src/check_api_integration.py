import boto3
import json
from pathlib import Path

apigateway = boto3.client('apigateway', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def check_api_integration():
    """Check API Gateway to Lambda integration"""
    
    print("="*80)
    print("🔍 CHECKING API GATEWAY INTEGRATION")
    print("="*80 + "\n")
    
    # Load API info
    with open('config/api_gateway_info.json', 'r') as f:
        api_info = json.load(f)
    
    api_id = api_info['api_id']
    print(f"API ID: {api_id}\n")
    
    # Get resources
    print("Step 1: Getting resources...")
    resources = apigateway.get_resources(restApiId=api_id)['items']
    
    for resource in resources:
        print(f"  Resource: {resource.get('pathPart', '/')}")
        if 'pathPart' in resource and resource['pathPart'] == 'generate':
            resource_id = resource['id']
            print(f"  ✅ Found /generate resource: {resource_id}\n")
    
    # Get methods
    print("Step 2: Getting POST method...")
    try:
        method = apigateway.get_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST'
        )
        print(f"  ✅ POST method exists\n")
    except:
        print(f"  ❌ POST method not found\n")
        return
    
    # Get integration
    print("Step 3: Checking integration...")
    try:
        integration = apigateway.get_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST'
        )
        print(f"  Integration Type: {integration.get('type')}")
        print(f"  URI: {integration.get('uri')}")
        print(f"  ✅ Integration exists\n")
    except Exception as e:
        print(f"  ❌ Integration issue: {e}\n")
        return
    
    # Check Lambda permissions
    print("Step 4: Checking Lambda permissions...")
    try:
        policy = lambda_client.get_policy(FunctionName='ai-assistant-model-abstraction')
        policy_doc = json.loads(policy['Policy'])
        print(f"  Lambda policy statements: {len(policy_doc.get('Statement', []))}")
        for stmt in policy_doc.get('Statement', []):
            if 'apigateway' in str(stmt.get('Principal', '')):
                print(f"  ✅ API Gateway permission found")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"  ⚠️  No policy found - may need to add permission\n")
    
    # Check method response
    print("Step 5: Checking method responses...")
    try:
        responses = apigateway.get_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='200'
        )
        print(f"  ✅ 200 response configured\n")
    except:
        print(f"  ⚠️  200 response may not be configured\n")
    
    # Check integration response
    print("Step 6: Checking integration response...")
    try:
        int_response = apigateway.get_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='200'
        )
        print(f"  ✅ 200 integration response configured\n")
    except:
        print(f"  ⚠️  Integration response may not be configured\n")
    
    print("="*80)
    print("Troubleshooting complete. Check above for any ❌ or ⚠️  issues.\n")

if __name__ == "__main__":
    check_api_integration()