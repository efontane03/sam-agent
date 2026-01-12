#!/usr/bin/env python3
"""
Quick Diagnostic Script
Run this to quickly identify what's wrong with your current Sam deployment
"""

import requests
import json
from typing import Dict
import sys


class QuickDiagnostic:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.issues_found = []
        self.session_id = "diagnostic_session"
    
    def run(self):
        """Run all diagnostic checks"""
        print("=" * 70)
        print("SAM AGENT - QUICK DIAGNOSTIC")
        print("=" * 70)
        print(f"Testing: {self.api_url}\n")
        
        # Test 1: API is reachable
        if not self.test_api_reachable():
            print("\n❌ CRITICAL: Cannot reach API")
            return
        
        # Test 2: The Romeo y Julieta bug
        self.test_romeo_bug()
        
        # Test 3: Context preservation
        self.test_context_preservation()
        
        # Test 4: Intent classification
        self.test_intent_classification()
        
        # Test 5: Session state
        self.test_session_state()
        
        # Summary
        self.print_summary()
    
    def test_api_reachable(self) -> bool:
        """Test if API is reachable"""
        print("TEST 1: API Reachability")
        print("-" * 70)
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is reachable")
                return True
        except:
            pass
        
        # Try the ask endpoint with a simple message
        try:
            response = requests.post(
                f"{self.api_url}/ask",
                json={"message": "hello", "session_id": self.session_id},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ API is reachable (via /ask endpoint)")
                return True
            else:
                print(f"❌ API returned status {response.status_code}")
                self.issues_found.append("API not responding correctly")
                return False
        
        except Exception as e:
            print(f"❌ Cannot reach API: {e}")
            self.issues_found.append(f"Cannot reach API: {e}")
            return False
    
    def test_romeo_bug(self):
        """Test the specific Romeo y Julieta bug"""
        print("\nTEST 2: Romeo y Julieta Bug (THE CRITICAL BUG)")
        print("-" * 70)
        
        # Reset session
        self.session_id = f"diagnostic_romeo_{int(__import__('time').time())}"
        
        # Turn 1: Ask about Romeo y Julieta
        response1 = self.send_message("tell me about romeo y julieta cigars")
        
        if not response1:
            print("❌ No response to first message")
            self.issues_found.append("Romeo bug test: No response")
            return
        
        print(f"Turn 1: 'tell me about romeo y julieta cigars'")
        print(f"Response preview: {response1[:150]}...")
        
        # Turn 2: Ask what bourbons pair with "it"
        response2 = self.send_message("what bourbons pair well with it")
        
        if not response2:
            print("❌ No response to second message")
            self.issues_found.append("Romeo bug test: No response to pairing question")
            return
        
        print(f"\nTurn 2: 'what bourbons pair well with it'")
        print(f"Response preview: {response2[:150]}...")
        
        # Check if response contains bourbon names (CORRECT)
        bourbon_keywords = ["buffalo trace", "eagle rare", "four roses", "woodford", "makers mark", "bourbon"]
        has_bourbon = any(kw in response2.lower() for kw in bourbon_keywords)
        
        # Check if response contains cigar names (WRONG)
        cigar_keywords = ["wrapper", "ring gauge", "nicaraguan", "connecticut shade", "smoke time"]
        has_cigar = any(kw in response2.lower() for kw in cigar_keywords)
        
        print(f"\nAnalysis:")
        print(f"  Contains bourbon keywords: {has_bourbon}")
        print(f"  Contains cigar keywords: {has_cigar}")
        
        if has_bourbon and not has_cigar:
            print("✅ PASSED - Returns bourbons correctly")
        else:
            print("❌ FAILED - Romeo y Julieta bug is present!")
            self.issues_found.append("Romeo bug: Returns cigars instead of bourbons for pairing request")
    
    def test_context_preservation(self):
        """Test if context is preserved"""
        print("\nTEST 3: Context Preservation")
        print("-" * 70)
        
        # Reset session
        self.session_id = f"diagnostic_context_{int(__import__('time').time())}"
        
        # Turn 1: Discuss cigars
        response1 = self.send_message("whats a mid-tier robust cigar")
        print("Turn 1: 'whats a mid-tier robust cigar'")
        print(f"Response: {response1[:100]}..." if response1 else "No response")
        
        # Turn 2: Ask for more options (with typo)
        response2 = self.send_message("give me mor robust optins")
        print("\nTurn 2: 'give me mor robust optins'")
        print(f"Response: {response2[:150]}..." if response2 else "No response")
        
        # Check if Sam asks "what are you looking for?" (BAD)
        asks_for_clarification = any(
            phrase in response2.lower() 
            for phrase in ["what are you looking for", "what would you like", "need more context"]
        )
        
        # Check if Sam provides recommendations (GOOD)
        provides_recommendations = any(
            cigar in response2.lower()
            for cigar in ["padron", "oliva", "cao", "liga privada"]
        )
        
        if provides_recommendations and not asks_for_clarification:
            print("✅ PASSED - Context preserved, provides recommendations")
        else:
            print("❌ FAILED - Context lost, asks for clarification")
            self.issues_found.append("Context not preserved across turns")
    
    def test_intent_classification(self):
        """Test intent classification (cigar retail vs bourbon allocation)"""
        print("\nTEST 4: Intent Classification")
        print("-" * 70)
        
        # Reset session
        self.session_id = f"diagnostic_intent_{int(__import__('time').time())}"
        
        # Establish cigar context
        response1 = self.send_message("tell me about Oliva Serie V cigars")
        print("Turn 1: 'tell me about Oliva Serie V cigars'")
        
        # Ask where to find them
        response2 = self.send_message("where can I find these near me")
        print("\nTurn 2: 'where can I find these near me'")
        print(f"Response: {response2[:200]}..." if response2 else "No response")
        
        # Check if mentions allocation (WRONG for cigars)
        mentions_allocation = "allocation" in response2.lower()
        
        # Check if asks for location or mentions cigar shops (CORRECT)
        appropriate_response = any(
            phrase in response2.lower()
            for phrase in ["location", "zip code", "city", "cigar shop", "tobacco shop"]
        )
        
        if appropriate_response and not mentions_allocation:
            print("✅ PASSED - Correctly identifies cigar retail search")
        else:
            print("❌ FAILED - Misclassifies as bourbon allocation")
            self.issues_found.append("Intent misclassification: cigar retail → bourbon allocation")
    
    def test_session_state(self):
        """Test if session state is accessible"""
        print("\nTEST 5: Session State Debugging")
        print("-" * 70)
        
        try:
            response = requests.get(f"{self.api_url}/debug/session/{self.session_id}", timeout=5)
            
            if response.status_code == 200:
                state = response.json()
                print("✅ Debug endpoint exists")
                print(f"Session state: {json.dumps(state, indent=2)[:300]}...")
            else:
                print("⚠️  Debug endpoint not found (expected if not implemented)")
        except Exception as e:
            print(f"⚠️  Debug endpoint not available: {e}")
    
    def send_message(self, message: str) -> str:
        """Send a message and return response"""
        try:
            response = requests.post(
                f"{self.api_url}/ask",
                json={"message": message, "session_id": self.session_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return ""
        except Exception as e:
            print(f"Error sending message: {e}")
            return ""
    
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 70)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 70)
        
        if not self.issues_found:
            print("🎉 No issues found! Phase 1 appears to be working correctly.")
        else:
            print(f"Found {len(self.issues_found)} issue(s):\n")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue}")
            
            print("\n" + "=" * 70)
            print("RECOMMENDED ACTIONS:")
            print("=" * 70)
            
            if any("Romeo bug" in issue for issue in self.issues_found):
                print("\n📋 Fix Romeo Bug:")
                print("   - Implement smart pronoun resolution")
                print("   - Track both last_bourbon and last_cigar contexts")
                print("   - See: IMPLEMENTATION_GUIDE.md - Step 3")
            
            if any("Context" in issue for issue in self.issues_found):
                print("\n📋 Fix Context Preservation:")
                print("   - Add typo correction")
                print("   - Implement subject inference from context")
                print("   - See: IMPLEMENTATION_GUIDE.md - Step 2")
            
            if any("Intent" in issue for issue in self.issues_found):
                print("\n📋 Fix Intent Classification:")
                print("   - Use IntentClassifier from cigar_retail_search.py")
                print("   - Add cigar retail search handler")
                print("   - See: IMPLEMENTATION_GUIDE.md - Step 3")
            
            print("\n📋 Next Steps:")
            print("   1. Review IMPLEMENTATION_GUIDE.md")
            print("   2. Add session debugging (session_debugger.py)")
            print("   3. Implement fixes from the guide")
            print("   4. Run verify_deployment.py to confirm")


if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    diagnostic = QuickDiagnostic(api_url)
    diagnostic.run()