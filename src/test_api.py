import requests
import json
from pathlib import Path
 
def load_api_endpoint():
    """Load API endpoint from config"""
    with open('config/api_gateway_info.json', 'r') as f:
        api_info = json.load(f)
    return api_info['endpoint']
 
def test_api():
    """Test the AI Assistant API"""
    
    endpoint = load_api_endpoint()
    
    print("="*80)
    print("🧪 TESTING AI ASSISTANT API")
    print("="*80)
    print(f"\nEndpoint: {endpoint}\n")
    
    test_cases = [
        {
            "name": "Financial Question",
            "prompt": "What is a 401(k) retirement plan? Explain briefly.",
            "use_case": "financial"
        },
        {
            "name": "General Knowledge",
            "prompt": "What is compound interest and how does it work?",
            "use_case": "general"
        },
        {
            "name": "Investment Question",
            "prompt": "What is an ETF and why would someone invest in one?",
            "use_case": "investment"
        },
        {
            "name": "Technology Question",
            "prompt": "What is machine learning?",
            "use_case": "technology"
        },
        {
            "name": "Cryptocurrency Question",
            "prompt": "What is cryptocurrency?",
            "use_case": "finance"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"  Question: {test['prompt'][:60]}...")
        
        payload = {
            "prompt": test['prompt'],
            "use_case": test['use_case']
        }
        
        try:
            # Add API Key header
            headers = {'x-api-key': 'your-secret-key-12345'}
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                model_used = data.get('model_used', 'Unknown')
                latency = data.get('latency', 'N/A')
                ai_response = data.get('response', '')[:100]
                
                print(f"  ✅ Model: {model_used}")
                print(f"  ✅ Latency: {latency}s")
                print(f"  ✅ Response: {ai_response}...\n")
                
                results.append({
                    "test": test['name'],
                    "status": "SUCCESS",
                    "model": model_used,
                    "latency": latency
                })
            else:
                error = response.json().get('error', 'Unknown error')
                print(f"  ❌ Error: {error}\n")
                
                results.append({
                    "test": test['name'],
                    "status": "FAILED",
                    "error": error
                })
        
        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout - Lambda took too long\n")
            results.append({
                "test": test['name'],
                "status": "TIMEOUT"
            })
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
            results.append({
                "test": test['name'],
                "status": "ERROR",
                "error": str(e)
            })
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"\nTests Passed: {successful}/{total}")
    
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"  {status_icon} {result['test']}: {result['status']}")
    
    print("\n" + "="*80)
    
    if successful == total:
        print("🎉 ALL TESTS PASSED! Your system is working!")
    elif successful > 0:
        print("⚠️  Some tests passed. Check failed tests above.")
    else:
        print("❌ No tests passed. Check Lambda and API Gateway configuration.")
    
    print("="*80 + "\n")
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✅ Results saved to test_results.json\n")
 
if __name__ == "__main__":
    test_api()
 