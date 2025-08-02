#!/usr/bin/env python3
"""
Test script for Grok API functionality
"""

import requests
import json

# Grok AI API Configuration
GROK_API_KEY = "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"
GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def test_grok_api():
    """Test Grok API with a simple query"""
    try:
        print("🧪 Testing Grok API Connection")
        print("=" * 50)
        
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful financial advisor chatbot for the Dabba expense tracker app. Provide personalized financial insights and advice based on the user's data."
                },
                {
                    "role": "user",
                    "content": "Hello! Can you help me with financial advice?"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print("📡 Making API request...")
        response = requests.post(GROK_API_URL, headers=headers, json=payload)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"🤖 Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ API call failed!")
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

def test_api_key_format():
    """Test if API key format is correct"""
    print("\n🔑 Testing API Key Format")
    print("=" * 30)
    
    if GROK_API_KEY.startswith("gsk_"):
        print("✅ API key format looks correct (starts with 'gsk_')")
    else:
        print("❌ API key format might be incorrect")
    
    print(f"📏 API key length: {len(GROK_API_KEY)} characters")
    print(f"🔐 API key: {GROK_API_KEY[:10]}...{GROK_API_KEY[-10:]}")

def main():
    """Run all tests"""
    print("🧪 Testing Grok API Functionality")
    print("=" * 50)
    
    # Test API key format
    test_api_key_format()
    
    # Test API call
    success = test_grok_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Grok API is working correctly!")
        print("✅ The chatbot should work properly.")
    else:
        print("⚠️  Grok API is not working.")
        print("📝 Possible issues:")
        print("   1. API key might be invalid or expired")
        print("   2. Network connectivity issues")
        print("   3. API rate limits exceeded")
        print("   4. Incorrect API endpoint")

if __name__ == "__main__":
    main() 