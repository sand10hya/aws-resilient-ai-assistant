import boto3
import json
import time
 
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
 
# Models to try, in order (fastest/cheapest first)
MODELS_TO_TRY = [
    'amazon.nova-lite-v1:0',
    'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    'us.anthropic.claude-sonnet-4-6'
]
 
def lambda_handler(event, context):
    """
    Lambda handler with fallback logic across 3 models.
    Tries Nova Lite -> Claude Haiku -> Claude Sonnet
    """
    try:
        body = json.loads(event.get('body', '{}'))
        prompt = body.get('prompt', '')
 
        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No prompt provided'})
            }
 
        for model_id in MODELS_TO_TRY:
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
    """Invoke a Bedrock model - handles Nova and Claude formats"""
 
    start_time = time.time()
 
    try:
        if 'claude' in model_id.lower():
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            })
        else:
            body = json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ]
            })
 
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
 
        response_body = json.loads(response['body'].read().decode())
 
        if 'claude' in model_id.lower():
            output = response_body['content'][0]['text']
        else:
            try:
                output = response_body['content'][0]['text']
            except (KeyError, IndexError, TypeError):
                try:
                    output = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
                except:
                    output = str(response_body)
 
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