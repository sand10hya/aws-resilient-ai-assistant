import boto3
import json
import time
import os
 
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
appconfig_client = boto3.client('appconfig', region_name='us-east-1')
VALID_API_KEY = os.environ.get('API_KEY', '')
 
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'OPTIONS,POST'
}
 
# Models to try, in order (fastest/cheapest first) - used as the fallback chain
MODELS_TO_TRY = [
    'amazon.nova-lite-v1:0',
    'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    'us.anthropic.claude-sonnet-4-6'
]
 
# Keywords that suggest a question needs deeper reasoning
COMPLEX_KEYWORDS = ['explain', 'why', 'compare', 'analyze', 'trade-off', 'tradeoff', 'pros and cons']
 
 
def choose_model(prompt, use_case='general'):
    """
    Rule-based router: decides which model to start with based on
    the use_case hint, prompt length, and keyword signals.
    Returns the STARTING model - if it fails, invoke_with_fallback()
    will still try the rest of MODELS_TO_TRY as a safety net.
    """
    use_case = (use_case or 'general').lower()
 
    # Rule 1: user already told us
    if use_case == 'complex':
        return 'us.anthropic.claude-sonnet-4-6'
    if use_case == 'simple':
        return 'amazon.nova-lite-v1:0'
 
    # Rule 2: long questions are usually more complex
    if len(prompt.split()) > 40:
        return 'us.anthropic.claude-sonnet-4-6'
 
    # Rule 3: keywords suggest deeper reasoning needed
    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in COMPLEX_KEYWORDS):
        return 'us.anthropic.claude-sonnet-4-6'
 
    # Default: simple factual question
    return 'amazon.nova-lite-v1:0'
 
 
def lambda_handler(event, context):
    """
    Lambda handler for AI Assistant
    Features:
    - API Key Authentication
    - Rate Limiting (10 requests per minute)
    - Rule-based smart routing (Nova Lite / Claude Haiku / Claude Sonnet)
    - Automatic fallback across models if the chosen model fails
    - CORS enabled (for browser-based demo page)
    """
 
    try:
        # Check API Key
        api_key = event.get('headers', {}).get('x-api-key', '')
        if api_key != VALID_API_KEY:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
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
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Rate limit exceeded: Max 10 requests per minute'})
            }
 
        # Parse request
        body = json.loads(event.get('body', '{}'))
        prompt = body.get('prompt', '')
        use_case = body.get('use_case', 'general')
 
        if not prompt:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'No prompt provided'})
            }
 
        # Decide starting model via rule-based router
        starting_model = choose_model(prompt, use_case)
 
        # Invoke with fallback across remaining models if needed
        result = invoke_with_fallback(starting_model, prompt)
 
        if result.get('success'):
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'model_used': result.get('model_used'),
                    'response': result.get('output'),
                    'latency': result.get('latency')
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': result.get('error')})
            }
 
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': str(e)})
        }
 
 
def invoke_with_fallback(starting_model, prompt):
    """
    Tries the starting_model first (chosen by the router).
    If it fails, falls back through the rest of MODELS_TO_TRY in order.
    Only returns an error if every model in the chain fails.
    """
    # Build the try-order: starting model first, then the rest of the chain
    # (skip duplicating the starting model if it's already in the list)
    try_order = [starting_model] + [m for m in MODELS_TO_TRY if m != starting_model]
 
    last_error = None
 
    for model_id in try_order:
        print(f"Trying model: {model_id}")
        response = invoke_bedrock_model(model_id, prompt)
 
        if response.get('success'):
            return {
                'success': True,
                'model_used': model_id,
                'output': response.get('output'),
                'latency': response.get('latency')
            }
        else:
            print(f"Model {model_id} failed: {response.get('error')}")
            last_error = response.get('error')
 
    # All models failed
    return {
        'success': False,
        'error': f'All models failed. Last error: {last_error}'
    }
 
 
def invoke_bedrock_model(model_id, prompt):
    """Invoke a Bedrock model - handles both Nova and Claude request/response formats"""
 
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
 
        # Try to extract output with error handling (Claude and Nova formats)
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
        print(f"Error invoking model: {str(e)}")
        print(f"Full error: {repr(e)}")
        return {
            'success': False,
            'error': f"Model error: {str(e)}",
            'latency': round(latency, 2)
        }