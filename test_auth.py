#!/usr/bin/env python3
"""
Test Azure Foundry authentication with different methods.
Run: python test_auth.py
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv('.env')

endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
key = os.getenv('AZURE_OPENAI_KEY')
deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1')

print(f"Endpoint: {endpoint}")
print(f"Key length: {len(key) if key else 0}")
print(f"Deployment: {deployment}\n")

# Test 1: Inference API path
print("=== Test 1: /inference/chat/completions ===")
url1 = f'{endpoint.rstrip("/")}/inference/chat/completions'
resp1 = requests.post(url1, headers={'api-key': key, 'Content-Type': 'application/json'}, 
                      json={'messages': [{'role': 'user', 'content': 'Hi'}], 'model': deployment}, timeout=10)
print(f"Status: {resp1.status_code}")
print(f"Response: {resp1.text[:300]}\n")

# Test 2: OpenAI-compatible path
print("=== Test 2: /openai/deployments/{deployment}/chat/completions ===")
url2 = f'{endpoint.rstrip("/")}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-01'
resp2 = requests.post(url2, headers={'api-key': key, 'Content-Type': 'application/json'},
                      json={'messages': [{'role': 'user', 'content': 'Hi'}]}, timeout=10)
print(f"Status: {resp2.status_code}")
print(f"Response: {resp2.text[:300]}\n")

# Test 3: Try with Authorization header
print("=== Test 3: Using Authorization: Bearer ===")
url3 = f'{endpoint.rstrip("/")}/inference/chat/completions'
resp3 = requests.post(url3, headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                      json={'messages': [{'role': 'user', 'content': 'Hi'}], 'model': deployment}, timeout=10)
print(f"Status: {resp3.status_code}")
print(f"Response: {resp3.text[:300]}\n")

print("If all tests fail with 401, please verify:")
print("1. The API key is correct from Azure AI Foundry portal")
print("2. The endpoint URL matches exactly what's shown in the portal")
print("3. The deployment name is correct")
