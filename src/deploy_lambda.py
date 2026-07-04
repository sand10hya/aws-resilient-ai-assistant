import boto3
import json
import zipfile
import os
from pathlib import Path

iam = boto3.client('iam', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
apigateway = boto3.client('apigateway', region_name='us-east-1')

REGION = 'us-east-1'
ROLE_NAME = 'lambda-bedrock-role'
FUNCTION_NAME = 'ai-assistant-model-abstraction'

def create_iam_role():
    """Create IAM role for Lambda"""
    
    print("Step 1: Creating IAM Role...")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role_response = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for AI Assistant Lambda function'
        )
        role_arn = role_response['Role']['Arn']
        print(f"✅ IAM Role created: {role_arn}\n")
    except iam.exceptions.EntityAlreadyExistsException:
        print("⚠️  Role already exists\n")
        role = iam.get_role(RoleName=ROLE_NAME)
        role_arn = role['Role']['Arn']
        print(f"✅ Using existing role: {role_arn}\n")
    
    # Attach policies
    print("Step 2: Attaching Policies...")
    
    policies = [
        'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
        'arn:aws:iam::aws:policy/AWSAppConfigReadOnlyAccess'
    ]
    
    for policy_arn in policies:
        try:
            iam.attach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn=policy_arn
            )
            print(f"✅ Attached: {policy_arn}")
        except iam.exceptions.NoSuchEntityException:
            print(f"⚠️  Policy not found: {policy_arn}")
    
    print()
    return role_arn

def package_lambda():
    """Package Lambda function as ZIP"""
    
    print("Step 3: Packaging Lambda Function...")
    
    zip_path = 'lambda_function.zip'
    
    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write('src/lambda_model_abstraction.py', 'lambda_model_abstraction.py')
    
    print(f"✅ Lambda function packaged: {zip_path}\n")
    
    return zip_path

def deploy_lambda(role_arn, zip_path):
    """Deploy Lambda function to AWS"""
    
    print("Step 4: Deploying Lambda to AWS...")
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_model_abstraction.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30,
            MemorySize=512,
            Description='AI Assistant Model Abstraction Layer',
            Environment={
                'Variables': {
                    'REGION': REGION,
                    'APP_NAME': 'AIAssistantApp',
                    'ENVIRONMENT': 'Production'
                }
            }
        )
        lambda_arn = response['FunctionArn']
        print(f"✅ Lambda function deployed: {lambda_arn}\n")
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️  Function already exists, updating...\n")
        response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_content
        )
        lambda_arn = response['FunctionArn']
        print(f"✅ Lambda function updated: {lambda_arn}\n")
    
    return lambda_arn

def add_api_gateway_permission(lambda_arn):
    """Add permission for API Gateway to invoke Lambda"""
    
    print("Step 5: Adding API Gateway Permission...")
    
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId='AllowAPIGateway',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com'
        )
        print("✅ API Gateway permission granted\n")
    except lambda_client.exceptions.ResourceConflictException:
        print("⚠️  Permission already exists\n")

def update_api_gateway_integration(lambda_arn):
    """Update API Gateway to call Lambda"""
    
    print("Step 6: Connecting API Gateway to Lambda...")
    
    try:
        # Load API info
        with open('config/api_gateway_info.json', 'r') as f:
            api_info = json.load(f)
        
        api_id = api_info['api_id']
        
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)['items']
        resource_id = next(r['id'] for r in resources if r.get('pathPart') == 'generate')
        
        # Update integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        print("✅ API Gateway integration updated\n")
        
    except Exception as e:
        print(f"⚠️  API Gateway update: {e}\n")

def cleanup():
    """Remove temporary ZIP file"""
    
    if os.path.exists('lambda_function.zip'):
        os.remove('lambda_function.zip')
        print("✅ Cleanup complete\n")

def main():
    """Main deployment flow"""
    
    print("="*80)
    print("🚀 DEPLOYING LAMBDA FUNCTION")
    print("="*80 + "\n")
    
    # Create IAM role
    role_arn = create_iam_role()
    
    # Package Lambda
    zip_path = package_lambda()
    
    # Deploy Lambda (wait a bit for role to propagate)
    import time
    print("Waiting for IAM role to propagate...")
    time.sleep(10)
    
    lambda_arn = deploy_lambda(role_arn, zip_path)
    
    # Add permissions
    add_api_gateway_permission(lambda_arn)
    
    # Update API Gateway
    update_api_gateway_integration(lambda_arn)
    
    # Cleanup
    cleanup()
    
    # Summary
    print("="*80)
    print("✅ LAMBDA DEPLOYMENT COMPLETE!")
    print("="*80)
    print(f"\nFunction Name: {FUNCTION_NAME}")
    print(f"Function ARN: {lambda_arn}")
    print(f"Role: {role_arn}")
    print("\nYour API is now connected to Lambda!")
    print("Ready to test in Step 3.5")
    print("\n" + "="*80)
    
    # Save deployment info
    deployment_info = {
        "function_name": FUNCTION_NAME,
        "function_arn": lambda_arn,
        "role_name": ROLE_NAME,
        "role_arn": role_arn,
        "region": REGION
    }
    
    with open('config/lambda_deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print("✅ Deployment info saved to config/lambda_deployment_info.json\n")

if __name__ == "__main__":
    main()