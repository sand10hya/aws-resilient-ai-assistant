import boto3
import json

logs_client = boto3.client('logs', region_name='us-east-1')

def check_lambda_logs():
    """Check Lambda function logs"""
    
    print("="*80)
    print("🔍 CHECKING LAMBDA LOGS")
    print("="*80 + "\n")
    
    log_group = '/aws/lambda/ai-assistant-model-abstraction'
    
    try:
        # Get log streams
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print("⚠️  No log streams found yet\n")
            return
        
        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"Latest log stream: {stream_name}\n")
        
        # Get log events
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=50
        )
        
        print("Recent Lambda logs:")
        print("-" * 80)
        
        for event in events['events']:
            message = event['message'].strip()
            print(f"{message}\n")
        
        print("="*80)
        
    except logs_client.exceptions.ResourceNotFoundException:
        print(f"⚠️  Log group not found: {log_group}")
        print("Lambda may not have been invoked yet or logs are still being created\n")
    except Exception as e:
        print(f"Error: {e}\n")

if __name__ == "__main__":
    check_lambda_logs()