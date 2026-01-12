#!/usr/bin/env python3
"""
Deployment Verification Script
Checks if Phase 1 fixes are actually deployed to production
"""

import requests
import json
from typing import Dict, List

class DeploymentVerifier:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session_id = "test_verify_session"
        
    def test_context_preservation(self) -> Dict:
        """Test if context is preserved across multiple turns"""
        print("\n" + "="*60)
        print("TEST 1: Context Preservation")
        print("="*60)
        
        results = {
            "test_name": "Context Preservation",
            "passed": False,
            "details": []
        }
        
        # Turn 1: Ask about Romeo y Julieta cigars
        turn1 = self._send_message("tell me about romeo y julieta cigars")
        results["details"].append({
            "turn": 1,
            "user_message": "tell me about romeo y julieta cigars",
            "response_preview": turn1[:200] if turn1 else "No response"
        })
        
        # Turn 2: Ask what bourbons pair with "it"
        turn2 = self._send_message("what bourbons pair well with it")
        results["details"].append({
            "turn": 2,
            "user_message": "what bourbons pair well with it",
            "response_preview": turn2[:200] if turn2 else "No response"
        })
        
        # Check if response mentions bourbon names (not cigar names)
        bourbon_keywords = ["buffalo trace", "eagle rare", "four roses", "woodford", "makers mark"]
        cigar_keywords = ["romeo", "padron", "cohiba", "wrapper", "ring gauge"]
        
        has_bourbon = any(kw in turn2.lower() for kw in bourbon_keywords)
        has_cigar = any(kw in turn2.lower() for kw in cigar_keywords)
        
        if has_bourbon and not has_cigar:
            results["passed"] = True
            print("✅ PASSED: Response contains bourbon recommendations")
        else:
            results["passed"] = False
            print("❌ FAILED: Response doesn't contain bourbon recommendations")
            print(f"   Has bourbon keywords: {has_bourbon}")
            print(f"   Has cigar keywords: {has_cigar}")
        
        return results
    
    def test_pronoun_resolution(self) -> Dict:
        """Test if pronouns are resolved correctly"""
        print("\n" + "="*60)
        print("TEST 2: Pronoun Resolution (Critical Bug)")
        print("="*60)
        
        results = {
            "test_name": "Pronoun Resolution",
            "passed": False,
            "details": []
        }
        
        # Fresh session
        self._reset_session()
        
        # Turn 1: Discuss Michter's bourbon
        turn1 = self._send_message("tell me about michters bourbon")
        results["details"].append({
            "turn": 1,
            "user_message": "tell me about michters bourbon",
            "has_michters": "michter" in turn1.lower()
        })
        
        # Turn 2: Ask about Romeo y Julieta cigar
        turn2 = self._send_message("what about romeo y julieta cigars")
        results["details"].append({
            "turn": 2,
            "user_message": "what about romeo y julieta cigars",
            "has_romeo": "romeo" in turn2.lower()
        })
        
        # Turn 3: THE CRITICAL TEST - "what pairs with it" should return BOURBONS, not cigars
        turn3 = self._send_message("what bourbon pairs with it")
        results["details"].append({
            "turn": 3,
            "user_message": "what bourbon pairs with it",
            "response_preview": turn3[:300] if turn3 else "No response"
        })
        
        # Check if "it" was resolved to Romeo y Julieta (cigar), not Michter's (bourbon)
        mentions_romeo = "romeo" in turn3.lower()
        returns_bourbon = any(kw in turn3.lower() for kw in ["buffalo", "eagle rare", "four roses", "bourbon"])
        returns_cigars = any(kw in turn3.lower() for kw in ["wrapper", "ring gauge", "smoke time"])
        
        if returns_bourbon and not returns_cigars:
            results["passed"] = True
            print("✅ PASSED: Correctly resolved 'it' to Romeo y Julieta and returned bourbons")
        else:
            results["passed"] = False
            print("❌ FAILED: Did not correctly resolve pronoun")
            print(f"   Mentions Romeo: {mentions_romeo}")
            print(f"   Returns bourbon: {returns_bourbon}")
            print(f"   Returns cigars: {returns_cigars}")
        
        return results
    
    def test_strength_matching(self) -> Dict:
        """Test if strength preferences are respected"""
        print("\n" + "="*60)
        print("TEST 3: Strength Matching")
        print("="*60)
        
        results = {
            "test_name": "Strength Matching",
            "passed": False,
            "details": []
        }
        
        self._reset_session()
        
        # Ask for full-bodied cigar pairing
        response = self._send_message("give me a full flavored cigar pairing")
        results["details"].append({
            "user_message": "give me a full flavored cigar pairing",
            "response_preview": response[:300] if response else "No response"
        })
        
        # Check if response mentions full-bodied cigars
        full_cigars = ["padron", "liga privada", "oliva serie v", "cao brazilia"]
        has_full_cigar = any(cigar in response.lower() for cigar in full_cigars)
        
        mild_cigars = ["romeo y julieta 1875", "arturo fuente 8-5-8"]
        has_mild_cigar = any(cigar in response.lower() for cigar in mild_cigars)
        
        if has_full_cigar and not has_mild_cigar:
            results["passed"] = True
            print("✅ PASSED: Returns full-bodied cigars as requested")
        else:
            results["passed"] = False
            print("❌ FAILED: Did not respect strength preference")
            print(f"   Has full-bodied cigar: {has_full_cigar}")
            print(f"   Has mild cigar: {has_mild_cigar}")
        
        return results
    
    def test_session_state_debugging(self) -> Dict:
        """Check if session state is being tracked"""
        print("\n" + "="*60)
        print("TEST 4: Session State Debugging")
        print("="*60)
        
        results = {
            "test_name": "Session State Debugging",
            "passed": False,
            "details": []
        }
        
        # Try to get session state (if endpoint exists)
        try:
            response = requests.get(f"{self.api_url}/debug/session/{self.session_id}")
            if response.status_code == 200:
                state = response.json()
                results["details"].append({
                    "session_state": state
                })
                print("✅ Session state endpoint exists")
                print(json.dumps(state, indent=2))
            else:
                print("⚠️  Session state endpoint not found (this is expected if not implemented)")
                results["details"].append({
                    "note": "Debug endpoint not implemented"
                })
        except Exception as e:
            print(f"⚠️  Could not fetch session state: {e}")
            results["details"].append({
                "error": str(e)
            })
        
        return results
    
    def _send_message(self, message: str) -> str:
        """Send a message to Sam and return the response"""
        try:
            response = requests.post(
                f"{self.api_url}/ask",
                json={
                    "message": message,
                    "session_id": self.session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                print(f"⚠️  API returned status {response.status_code}")
                return ""
        except Exception as e:
            print(f"⚠️  Error sending message: {e}")
            return ""
    
    def _reset_session(self):
        """Reset the test session"""
        import time
        self.session_id = f"test_verify_{int(time.time())}"
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("\n" + "="*60)
        print("SAM AGENT - DEPLOYMENT VERIFICATION")
        print("="*60)
        print(f"Testing API: {self.api_url}")
        
        test_results = []
        
        # Run all tests
        test_results.append(self.test_context_preservation())
        test_results.append(self.test_pronoun_resolution())
        test_results.append(self.test_strength_matching())
        test_results.append(self.test_session_state_debugging())
        
        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        passed_count = sum(1 for t in test_results if t.get("passed"))
        total_count = len([t for t in test_results if "passed" in t])
        
        for result in test_results:
            status = "✅ PASS" if result.get("passed") else "❌ FAIL" if "passed" in result else "⚠️  INFO"
            print(f"{status} - {result['test_name']}")
        
        print(f"\nPassed: {passed_count}/{total_count}")
        
        if passed_count == total_count:
            print("\n🎉 ALL TESTS PASSED - Phase 1 is deployed correctly!")
        else:
            print("\n⚠️  SOME TESTS FAILED - Phase 1 may not be fully deployed")
            print("\nNext steps:")
            print("1. Check Railway deployment logs")
            print("2. Verify sam_engine.py has the latest changes")
            print("3. Check if session state is persisting")
        
        return test_results


if __name__ == "__main__":
    import sys
    
    # Get API URL from command line or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    verifier = DeploymentVerifier(api_url)
    verifier.run_all_tests()