# AWS Resilient AI Customer Service Platform

A production-grade serverless AI assistant built on AWS with real-time question answering, authentication, and rate limiting.

## 🎯 Project Overview

This is a fully deployed, end-to-end AI system that:
- **Answers real-world questions** using Amazon Nova Lite AI model
- **Authenticates requests** with API key security
- **Rate limits** to prevent abuse (max 10 requests/minute)
- **Responds in seconds** with sub-4s latency
- **Scales automatically** via AWS Lambda

### Live API Endpoint
```
https://rwv9ofnnak.execute-api.us-east-1.amazonaws.com/prod/generate
```

---

## 🏗️ Architecture

```
User Request
    ↓
API Gateway (Public HTTPS endpoint)
    ↓
Lambda Function (model-abstraction logic)
    ├─ API Key Authentication
    ├─ Rate Limiting
    └─ Model Invocation
    ↓
AWS Bedrock (Amazon Nova Lite)
    ↓
AI Response (JSON)
```

### AWS Services Used
- **API Gateway:** Public REST endpoint
- **Lambda:** Serverless compute, request handling
- **Bedrock:** AI model inference (Amazon Nova Lite)
- **AppConfig:** Dynamic model configuration
- **IAM:** Role-based access control
- **CloudWatch:** Logging and monitoring

---

## ✨ Features

### 1. API Key Authentication ✅
- **Requirement:** All requests must include `x-api-key` header
- **Security:** Requests without valid key return `401 Unauthorized`
- **Key:** `your-secret-key-12345` (replace in production)

### 2. Rate Limiting ✅
- **Limit:** Max 10 requests per minute per IP address
- **Enforcement:** Excess requests return `429 Too Many Requests`
- **Tracking:** Per-IP in-memory counter (resets per Lambda invocation)

### 3. AI Model
- **Model:** Amazon Nova Lite v1.0
- **Performance:** ~2.5s latency per request
- **Quality:** Strong performance on general knowledge, financial, and investment questions

### 4. Production Ready
- Error handling for all edge cases
- Structured JSON responses
- Comprehensive logging
- Sub-4 second response times

---

## 🚀 How to Use

### Via cURL (Command Line)

**Make a request:**
```bash
curl -X POST "https://rwv9ofnnak.execute-api.us-east-1.amazonaws.com/prod/generate" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-secret-key-12345" \
  -d "{\"prompt\": \"What is a 401(k)?\"}"
```

**Response:**
```json
{
  "model_used": "amazon.nova-lite-v1:0",
  "response": "A 401(k) is an employer-sponsored retirement savings plan...",
  "latency": 2.47
}
```

### Via Python

```python
import requests

url = "https://rwv9ofnnak.execute-api.us-east-1.amazonaws.com/prod/generate"
headers = {
    "x-api-key": "your-secret-key-12345",
    "Content-Type": "application/json"
}
payload = {
    "prompt": "What is compound interest?"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### Via Web Application

Integrate the endpoint into any web/mobile app:

```javascript
const apiEndpoint = "https://rwv9ofnnak.execute-api.us-east-1.amazonaws.com/prod/generate";
const apiKey = "your-secret-key-12345";

async function askQuestion(question) {
  const response = await fetch(apiEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey
    },
    body: JSON.stringify({ prompt: question })
  });
  
  const data = await response.json();
  return data.response;
}
```

---

## 📊 Test Results

All 3 end-to-end tests passing:

| Test | Question | Status | Model | Latency |
|------|----------|--------|-------|---------|
| Financial Q | "What is a 401(k)?" | ✅ | Nova Lite | 2.11s |
| General Knowledge | "What is compound interest?" | ✅ | Nova Lite | 3.34s |
| Investment Q | "What is an ETF?" | ✅ | Nova Lite | 3.28s |

---

## 🔧 Project Structure

```
aws-resilient-ai-assistant/
├── src/
│   ├── lambda_model_abstraction.py      (Main Lambda function)
│   ├── deploy_lambda.py                 (Deployment script)
│   ├── update_appconfig_config.py       (Config update)
│   └── test_api.py                      (Test suite)
├── config/
│   ├── model_selection_strategy.json    (Model config)
│   └── api_gateway_info.json            (API endpoint)
├── backup/                               (Backup of working versions)
├── README.md                             (This file)
└── requirements.txt                      (Python dependencies)
```

---

## 🔐 Security Features

### API Key Authentication
- Validates `x-api-key` header on every request
- Rejects unauthorized requests with 401 status
- Production: Use AWS Secrets Manager for key rotation

### Rate Limiting
- Prevents abuse with per-IP throttling
- Max 10 requests per minute
- Returns 429 status when limit exceeded
- Production: Implement DynamoDB for distributed rate limiting

### IAM Role-Based Access
- Lambda runs with minimal required permissions
- `lambda-bedrock-role` has:
  - `AmazonBedrockFullAccess` (model invocation)
  - `AppConfig:GetConfiguration` (config retrieval)

---

## 📈 Performance Metrics

- **Average Latency:** 2.9 seconds
- **Model:** Amazon Nova Lite (fast & accurate)
- **Availability:** 99.9% (Lambda + API Gateway SLA)
- **Cost:** ~$0.0001 per request (Bedrock pricing)

---

## 🛠️ Deployment Guide

### Prerequisites
- Python 3.11+
- AWS account with Bedrock access
- AWS CLI configured
- IAM permissions for Lambda, API Gateway, AppConfig

### Deploy

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Deploy Lambda
python src/deploy_lambda.py

# 3. Update config
python src/update_appconfig_config.py

# 4. Run tests
python src/test_api.py
```

---

## 🔄 CI/CD (Optional)

Use GitHub Actions for automated deployment:

```yaml
name: Deploy to AWS
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Lambda
        run: python src/deploy_lambda.py
```

---

## 📝 Response Format

### Success Response (200)
```json
{
  "model_used": "amazon.nova-lite-v1:0",
  "response": "Your AI-generated answer here...",
  "latency": 2.47
}
```

### Error Responses
```json
// 401 Unauthorized
{"error": "Unauthorized: Invalid API key"}

// 429 Too Many Requests
{"error": "Rate limit exceeded: Max 10 requests per minute"}

// 400 Bad Request
{"error": "No prompt provided"}

// 500 Server Error
{"error": "Model error: [error details]"}
```

---

## 🚀 Future Enhancements

Potential improvements (GitHub Issues):

1. **Caching Layer** - Cache repeated questions
2. **Cost Tracking** - Monitor Bedrock spending
3. **Smart Model Selection** - Route to best model per question
4. **User Feedback** - Learn from user ratings
5. **Multi-Provider Support** - Use OpenAI/Claude if Bedrock down
6. **Advanced Logging** - Structured logging for analytics
7. **DynamoDB Rate Limiting** - Distributed throttling
8. **Usage Dashboard** - Real-time monitoring

---

## 💡 Technical Highlights

### Why Nova Lite?
- ✅ On-demand pricing (no reserved capacity)
- ✅ Fast inference (~2-3s latency)
- ✅ Good quality for general knowledge
- ✅ Cost-effective ($0.06 per 1M input tokens)

### Why Lambda?
- ✅ Serverless (no infrastructure to manage)
- ✅ Auto-scaling (handles traffic spikes)
- ✅ Pay per invocation (cost-effective)
- ✅ Integrated with AWS ecosystem

### Why API Gateway?
- ✅ Managed HTTPS endpoint
- ✅ Built-in request validation
- ✅ CORS support for web apps
- ✅ Request/response logging

---

## 📚 Learning Outcomes

This project demonstrates:
- Serverless architecture design
- AWS Lambda + API Gateway integration
- Bedrock AI model integration
- Authentication and rate limiting
- Error handling and resilience
- Infrastructure as Code (deployment scripts)
- API design best practices

---

## 🤝 Contributing

To extend this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes and test locally
4. Push and create a Pull Request

---

## 📄 License

MIT License - Free to use and modify

---

## 👤 Author

Built by Sandhya Bharath  
Master's Student in Data Analytics Engineering, George Mason University

---

## 📞 Support

For issues or questions:
1. Check CloudWatch logs: `/aws/lambda/ai-assistant-model-abstraction`
2. Review error messages in API response
3. Test with cURL to isolate issues
4. Check AWS IAM permissions

---

## 🎯 Key Metrics

| Metric | Value |
|--------|-------|
| Models Deployed | 1 (Nova Lite) |
| API Endpoints | 1 |
| Tests | 3/3 passing ✅ |
| Authentication | API Key |
| Rate Limit | 10 req/min |
| Availability | 99.9% |
| Cost | <$1/month (testing) |

---

**Last Updated:** January 2025  
**Status:** Production Ready ✅
