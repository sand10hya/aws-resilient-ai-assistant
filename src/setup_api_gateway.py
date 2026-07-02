import boto3
import json

apigateway = boto3.client('apigateway', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def setup_api_gateway():
    """Set up API Gateway for AI Assistant"""
    
    print("🔧 Setting up API Gateway...\n")
    
    # Step 1: Create REST API
    print("Step 1: Creating REST API...")
    try:
        api_response = apigateway.create_rest_api(
            name='AIAssistantAPI',
            description='AI Assistant with Dynamic Model Selection',
            endpointConfiguration={'types': ['REGIONAL']}
        )
        api_id = api_response['id']
        print(f"✅ API created: {api_id}\n")
    except apigateway.exceptions.BadRequestException:
        print("⚠️  API already exists, fetching existing API...\n")
        apis = apigateway.get_rest_apis(limit=100)['items']
        api_id = next((api['id'] for api in apis if api['name'] == 'AIAssistantAPI'), None)
        if not api_id:
            print("❌ Could not find existing API")
            return
    
    # Step 2: Get root resource
    print("Step 2: Getting root resource...")
    resources = apigateway.get_resources(restApiId=api_id)['items']
    root_id = resources[0]['id']
    print(f"✅ Root resource ID: {root_id}\n")
    
    # Step 3: Create /generate resource
    print("Step 3: Creating /generate resource...")
    try:
        resource_response = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='generate'
        )
        resource_id = resource_response['id']
        print(f"✅ Resource created: {resource_id}\n")
    except apigateway.exceptions.ConflictException:
        print("⚠️  Resource already exists\n")
        resource_id = next(r['id'] for r in resources if r.get('pathPart') == 'generate')
    
    # Step 4: Create POST method
    print("Step 4: Creating POST method...")
    try:
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE'
        )
        print("✅ POST method created\n")
    except apigateway.exceptions.BadRequestException:
        print("⚠️  POST method already exists\n")
    
    # Step 5: Set up Lambda integration
    print("Step 5: Setting up Lambda integration...")
    
    # Get Lambda function ARN
    try:
        lambda_response = lambda_client.get_function(FunctionName='ai-assistant-model-abstraction')
        lambda_arn = lambda_response['Configuration']['FunctionArn']
        print(f"✅ Lambda ARN: {lambda_arn}\n")
    except lambda_client.exceptions.ResourceNotFoundException:
        print("⚠️  Lambda function 'ai-assistant-model-abstraction' not found yet")
        print("   You'll need to deploy the Lambda function first in AWS console\n")
        lambda_arn = "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:ai-assistant-model-abstraction"
    
    try:
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        print("✅ Lambda integration configured\n")
    except Exception as e:
        print(f"⚠️  Integration setup: {str(e)}\n")
    
    # Step 6: Create deployment
    print("Step 6: Creating API deployment...")
    try:
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Production deployment'
        )
        print(f"✅ Deployment created\n")
    except apigateway.exceptions.BadRequestException:
        print("⚠️  Deployment already exists\n")
    
    # Step 7: Print API endpoint
    print("="*80)
    print("✅ API Gateway Setup Complete!")
    print("="*80)
    print(f"\nAPI Endpoint: https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/generate")
    print("\nTest with curl:")
    print(f'curl -X POST https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/generate \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"prompt": "What is a 401k?", "use_case": "financial"}\'')
    print("\n" + "="*80)
    
    # Save API info to file
    api_info = {
        "api_id": api_id,
        "endpoint": f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/generate",
        "region": "us-east-1"
    }
    
    with open('config/api_gateway_info.json', 'w') as f:
        json.dump(api_info, f, indent=2)
    
    print("✅ API info saved to config/api_gateway_info.json\n")

if __name__ == "__main__":
    setup_api_gateway()