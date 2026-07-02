import boto3
import json
import time
import os
 
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
appconfig_client = boto3.client('appconfig', region_name='us-east-1')
VALID_API_KEY = os.environ.get('API_KEY', '')
 
def lambda_handler(event, context):
    """
    Lambda handler for AI Assistant
    Features:
    - API Key Authentication
    - Rate Limiting (10 requests per minute)
    - Nova Lite model
    """
    
    try:
        # Check API Key
        api_key = event.get('headers', {}).get('x-api-key', '')
        if api_key != VALID_API_KEY:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized: Invalid API key'})
            }
        
        # Check Rate Limit (max 10 requests per minute per IP)
        client_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        
        if not hasattr(lambda_handler, 'request_counts'):
            lambda_handler.request_counts = {}
        
        if client_ip not in lambda_handler.request_counts:
            lambda_handler.request_counts[client_ip] = 0
        
        lambda_handler.request_counts[client_ip] += 1
        
        if lambda_handler.request_counts[client_ip] > 10:
            return {
                'statusCode': 429,
                'body': json.dumps({'error': 'Rate limit exceeded: Max 10 requests per minute'})
            }
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        prompt = body.get('prompt', '')
        use_case = body.get('use_case', 'general')
        
        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No prompt provided'})
            }
        
        # Use Nova Lite (on-demand supported)
        model_id = 'amazon.nova-lite-v1:0'
        
        # Invoke model
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
            return {
                'statusCode': 500,
                'body': json.dumps({'error': response.get('error')})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
 
def invoke_bedrock_model(model_id, prompt):
    """Invoke Amazon Nova model"""
    
    start_time = time.time()
    
    try:
        # Nova format: content is array of objects with "text" field
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
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode())
        
        # Try to extract output with error handling
        try:
            output = response_body['content'][0]['text']
        except (KeyError, IndexError, TypeError):
            # Fallback: try alternative structure
            try:
                output = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            except:
                # Last resort: stringify entire response
                output = str(response_body)
        
        latency = time.time() - start_time
        
        return {
            'success': True,
            'output': output,
            'latency': round(latency, 2)
        }
    
    except Exception as e:
        latency = time.time() - start_time
        print(f"Error invoking model: {str(e)}")
        print(f"Full error: {repr(e)}")
        return {
            'success': False,
            'error': f"Model error: {str(e)}",
            'latency': round(latency, 2)
        }
 