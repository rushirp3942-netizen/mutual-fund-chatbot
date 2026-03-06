"""Test script for chatbot fixes"""

import requests
import json

BASE_URL = "http://localhost:8002"

def test_query(description, message):
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Query: {message}")
    print('='*60)
    
    try:
        response = requests.post(f'{BASE_URL}/chat', json={'message': message})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['message']['content']
            sources = data.get('sources', [])
            
            print(f"\nResponse:\n{content}")
            
            if sources:
                print(f"\nSources:")
                for src in sources:
                    print(f"  - {src.get('fund_name', 'Unknown')}: {src.get('source_url', 'N/A')}")
            else:
                print("\nSources: None")
                
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

# Run tests
print("CHATBOT FIX VERIFICATION TESTS")
print("="*60)

# Test 1: Previously missing fund - Bandhan
test_query("Bandhan Small Cap - Expense Ratio", 
           "What is the expense ratio of Bandhan Small Cap Fund?")

# Test 2: Previously missing fund - Parag Parikh
test_query("Parag Parikh - Minimum SIP", 
           "What is the minimum SIP for Parag Parikh Flexi Cap Fund?")

# Test 3: Previously missing fund - ICICI Prudential
test_query("ICICI Prudential - Benchmark", 
           "What is the benchmark for ICICI Prudential Large Cap Fund?")

# Test 4: Previously missing fund - Tata
test_query("Tata Small Cap - Risk Level", 
           "What is the risk level of Tata Small Cap Fund?")

# Test 5: Previously missing fund - Axis
test_query("Axis Small Cap - Exit Load", 
           "What is the exit load for Axis Small Cap Fund?")

# Test 6: Previously missing fund - SBI Small Cap
test_query("SBI Small Cap - Lock-in Period", 
           "What is the lock-in period for SBI Small Cap Fund?")

# Test 7: Out of scope question
test_query("Out of Scope - Weather", 
           "What is the weather today?")

# Test 8: Out of scope - Sports
test_query("Out of Scope - Sports", 
           "Who won the cricket match yesterday?")

# Test 9: Investment advice (should be blocked)
test_query("Investment Advice - Should I invest", 
           "Should I invest in SBI ELSS?")

# Test 10: ELSS Lock-in (special handling)
test_query("ELSS Lock-in Period", 
           "What is the lock-in period for SBI ELSS?")

# Test 11: General question (should list all funds)
test_query("General Question", 
           "What funds do you have?")

# Test 12: Download statement
test_query("Download Statement", 
           "How do I download statement for HDFC Mid Cap?")

print("\n" + "="*60)
print("TESTING COMPLETE")
print("="*60)
