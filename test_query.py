import requests
import json

url = "http://localhost:8000/query"
payload = {
    "profile": {
        "age": 21,
        "income": 150000.0,
        "category": "SC",
        "state": "Rajasthan",
        "student": True
    },
    "question": "Which schemes am I eligible for?",
    "top_k": 5
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
