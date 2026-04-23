# SDK Generation Guide

## Prerequisites
- Node.js installed
- Backend running at http://localhost:8000

## Generate SDK

```bash
# Install the OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli

# Generate the Python SDK from the live API spec
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o exam_sdk

# Install the generated SDK
pip install -e exam_sdk/
```

## Use the SDK

```python
from exam_sdk.api.exams_api import ExamsApi
from exam_sdk import ApiClient, Configuration

config = Configuration(host="http://localhost:8000")
client = ApiClient(configuration=config)
api = ExamsApi(client)

# Create exam
exam = api.create_exam_exams_post({"title": "ML Test", "duration": 60})
print(exam)

# Submit
result = api.submit_exam_exams_id_submit_post(exam.id, {
    "user_name": "alice",
    "answers": {"q1": "answer here"},
    "time_taken_seconds": 1800,
    "paste_detected": False
})
print(result)
```

## Run the Demo Script

```bash
# With backend running:
cd sdk_usage
python demo.py
```
