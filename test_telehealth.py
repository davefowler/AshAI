#!/usr/bin/env python3
"""
Test script for the new telehealth and evaluation endpoints
"""

import requests
import json


def test_telehealth_endpoint():
    """Test the /ashai telehealth endpoint"""
    print("Testing /ashai telehealth endpoint...")
    
    url = "http://localhost:8000/ashai"
    
    data = {
        "messages": [
            {"role": "user", "content": "hello, i am pregnant"},
            {"role": "user", "content": "can i eat banana?"}
        ],
        "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Telehealth endpoint working!")
        print(f"Response: {result['response'][:100]}...")
        print(f"Sources: {len(result['sources'])} sources found")
        print(f"FAQs: {len(result['faqs'])} FAQs used")
        
        return result['response']
        
    except Exception as e:
        print(f"❌ Error testing telehealth endpoint: {e}")
        return None


def test_evaluator_endpoint(response_text):
    """Test the /evaluator endpoint"""
    print("\nTesting /evaluator endpoint...")
    
    url = "http://localhost:8000/evaluator"
    
    data = {
        "response": response_text,
        "context": "Patient asked about eating bananas during pregnancy",
        "profile": "Name: Ann\nLocation: Kerala India\nLanguage: Hindi\nCategory: Prenatal\nPatient History: They have had issues with itching."
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Evaluator endpoint working!")
        print(f"Medical Accuracy: {result['medical_accuracy']:.1f}%")
        print(f"Precision: {result['precision']:.1f}%")
        print(f"Language Clarity: {result['language_clarity']:.1f}%")
        print(f"Empathy Score: {result['empathy_score']:.1f}%")
        print(f"Overall Score: {result['overall_score']:.1f}%")
        print(f"Feedback: {result['feedback'][:100]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing evaluator endpoint: {e}")
        return None


def test_faq_endpoint():
    """Test the existing /faq endpoint for comparison"""
    print("\nTesting /faq endpoint...")
    
    url = "http://localhost:8000/faq"
    
    data = {
        "query": "pregnancy nutrition guidelines",
        "max_results": 2
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        print("✅ FAQ endpoint working!")
        print(f"Found {result['total_results']} results")
        
        for i, faq in enumerate(result['results'], 1):
            print(f"  {i}. {faq['question'][:50]}...")
            print(f"     Sources: {len(faq['sources'])}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing FAQ endpoint: {e}")
        return None


def main():
    """Run all tests"""
    print("🧪 Testing WebFAQMCP New Endpoints")
    print("=" * 50)
    
    # Test FAQ endpoint first
    faq_result = test_faq_endpoint()
    
    # Test telehealth endpoint
    telehealth_response = test_telehealth_endpoint()
    
    # Test evaluator endpoint if we got a response
    if telehealth_response:
        evaluation_result = test_evaluator_endpoint(telehealth_response)
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")
    
    if telehealth_response and evaluation_result:
        print("✅ All new endpoints are working correctly!")
    else:
        print("⚠️  Some endpoints may need attention.")


if __name__ == "__main__":
    main() 