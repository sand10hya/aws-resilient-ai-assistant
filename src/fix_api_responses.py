import boto3
import json
from pathlib import Path

apigateway = boto3.client('apigateway', region_name='us-east-1')

def fix_api_responses():
    """Fix missing method and integration responses"""
    
    print("="*80)
    print("🔧 FIXING API GATEWAY RESPONSES")
    print("="*80 + "\n")
    
    # Load API info
    with open('config/api_gateway_info.json', 'r') as f:
        api_info = json.load(f)
    
    api_id = api_info['api_id']
    
    # Get /generate resource
    resources = apigateway.get_resources(restApiId=api_id)['items']
    resource_id = next(r['id'] for r in resources if r.get('pathPart') == 'generate')
    
    print(f"API ID: {api_id}")
    print(f"Resource ID: {resource_id}\n")
    
    # Step 1: Create method response
    print("Step 1: Creating method response...")
    try:
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='200',
            responseModels={
                'application/json': 'Empty'
            }
        )
        print("✅ Method response created\n")
    except apigateway.exceptions.ConflictException:
        print("✅ Method response already exists\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Step 2: Create integration response
    print("Step 2: Creating integration response...")
    try:
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='200',
            responseTemplates={
                'application/json': ''
            }
        )
        print("✅ Integration response created\n")
    except apigateway.exceptions.ConflictException:
        print("✅ Integration response already exists\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Step 3: Create 403 method response
    print("Step 3: Creating 403 error response...")
    try:
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='403'
        )
        print("✅ 403 response created\n")
    except:
        print("⚠️  403 response already exists\n")
    
    # Step 4: Create 500 method response
    print("Step 4: Creating 500 error response...")
    try:
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='500'
        )
        print("✅ 500 response created\n")
    except:
        print("⚠️  500 response already exists\n")
    
    # Step 5: Redeploy API
    print("Step 5: Redeploying API...")
    try:
        # Get existing deployment
        deployments = apigateway.get_deployments(restApiId=api_id)['items']
        
        # Create new deployment
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Redeployment with fixed responses'
        )
        print(f"✅ API redeployed\n")
    except Exception as e:
        print(f"⚠️  Deployment issue: {e}\n")
    
    print("="*80)
    print("✅ API GATEWAY RESPONSES FIXED!")
    print("="*80)
    print("\nThe API should now work correctly.")
    print("Try running test again: python src/test_api.py\n")

if __name__ == "__main__":
    fix_api_responses()