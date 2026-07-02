from fallback_logic_v2 import lambda_handler
import json

# Simulate a request
test_event = {
    "body": json.dumps({
        "prompt": "What is a 401(k) retirement plan?"
    })
}

result = lambda_handler(test_event, None)

print("Status Code:", result['statusCode'])
print("Response Body:")
print(json.dumps(json.loads(result['body']), indent=2))