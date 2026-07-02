import boto3
import json
import time
 
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
appconfig_client = boto3.client('appconfig', region_name='us-east-1')
 
def lambda_handler(event, context):
    """
    Lambda handler for AI Assistant
    Tries multiple models: Nova Lite, Claude Haiku, Claude Sonnet
    """
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        prompt = body.get('prompt', '')
        use_case = body.get('use_case', 'general')
        
        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No prompt provided'})
            }
        
        # Models to try in order
        models_to_try = [
            'amazon.nova-lite-v1:0',
            'us.anthropic.claude-haiku-4-5-20251001-v1:0',
            'us.anthropic.claude-sonnet-4-6'
        ]
        
        # Try each model
        for model_id in models_to_try:
            print(f"Trying model: {model_id}")
            response = invoke_bedrock_model(model_id, prompt)
            
            if response.get('success'):
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'model_used': model_id,
                        'response': response.get('output'),
                        'latency': response.get('latency')
                    })
                }
            else:
                print(f"Model {model_id} failed: {response.get('error')}")
        
        # All models failed
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'All models failed'})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
 
def invoke_bedrock_model(model_id, prompt):
    """Invoke Bedrock model - handles Nova and Claude formats"""
    
    start_time = time.time()
    
    try:
        # Format request based on model type
        if 'claude' in model_id.lower():
            # Claude format
            body = json.dumps({
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            })
        else:
            # Nova format (content as array of objects with text field)
            body = json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            })
        
        # Invoke model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode())
        
        # Extract output based on model type
        if 'claude' in model_id.lower():
            output = response_body['content'][0]['text']
        else:
            # Nova response
            output = response_body.get('content', [{}])[0].get('text', '')
        
        latency = time.time() - start_time
        
        return {
            'success': True,
            'output': output,
            'latency': round(latency, 2)
        }
    
    except Exception as e:
        latency = time.time() - start_time
        print(f"Error with {model_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'latency': round(latency, 2)
        }