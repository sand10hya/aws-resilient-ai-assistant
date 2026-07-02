import boto3
import json
import time
 
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
appconfig_client = boto3.client('appconfig', region_name='us-east-1')
 
def lambda_handler(event, context):
    """
    Lambda handler for AI Assistant
    Uses Amazon Nova Lite model (on-demand supported)
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
    """Invoke Amazon Nova model - handle response parsing correctly"""
    
    start_time = time.time()
    
    try:
        # Nova format: content is array of objects with just "text" field
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
        
        # Extract output from Nova response - handle different response formats
        try:
            # Try primary format
            output = response_body['content'][0]['text']
        except (KeyError, IndexError, TypeError):
            try:
                # Try alternative format
                output = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            except:
                # Last resort - just stringify the response
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
        print(f"Response body: {response_body if 'response_body' in locals() else 'No response'}")
        return {
            'success': False,
            'error': str(e),
            'latency': round(latency, 2)
        }