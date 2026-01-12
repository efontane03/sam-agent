# Implementation Guide: Fixing the Failed Conversation Issues

## Overview
This guide walks through implementing fixes for the three major issues identified in the failed Sam conversation:

1. **Context Loss** - "give me mor robust optins" → Sam asks "what are you looking for?"
2. **Intent Misclassification** - "where can I find these cigars" → Sam thinks bourbon allocation
3. **Session State Not Persisting** - Context resets between turns

---

## STEP 1: Add Session Debugging (Do This First!)

### 1.1 Add debugging to your FastAPI app

**File: `api_handler.py`**

```python
from session_debugger import add_debug_endpoints, debugger

# After creating FastAPI app
app = FastAPI()
add_debug_endpoints(app)  # Adds /debug/session endpoints

# In your /ask endpoint
@app.post("/ask")
async def ask_sam(request: AskRequest):
    # Log incoming request
    debugger.log_session_state(
        request.session_id,
        "request_received",
        {
            "user_message": request.message,
            "session_id": request.session_id
        }
    )
    
    # Get or create session
    session = sam_engine.get_session(request.session_id)
    
    # Log session state BEFORE processing
    debugger.log_session_state(
        request.session_id,
        "before_processing",
        {
            "last_bourbon": session.last_bourbon_discussed,
            "last_cigar": session.last_cigar_discussed,
            "conversation_history_length": len(session.conversation_history)
        }
    )
    
    # Process message
    response = sam_engine.handle_message(session, request.message)
    
    # Log session state AFTER processing
    debugger.log_session_state(
        request.session_id,
        "after_processing",
        {
            "last_bourbon": session.last_bourbon_discussed,
            "last_cigar": session.last_cigar_discussed,
            "response_preview": response[:200]
        }
    )
    
    return {"response": response}
```

### 1.2 Test the debug endpoints

```bash
# Start your server
python api_handler.py

# Send a test message
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "tell me about romeo y julieta", "session_id": "debug_test"}'

# Check debug info
curl http://localhost:8000/debug/session/debug_test
```

This will show you EXACTLY what's happening with session state.

---

## STEP 2: Fix Context Loss (Typo Tolerance + Context Inference)

### 2.1 Add typo correction

**File: `sam_engine.py`**

```python
class MessagePreprocessor:
    """Preprocess messages before parsing"""
    
    COMMON_TYPOS = {
        "mor": "more",
        "optins": "options",
        "optoins": "options",
        "fid": "find",
        "thse": "these",
        "cigr": "cigar",
        "burboun": "bourbon",
        "whisy": "whisky",
        "recomendation": "recommendation",
    }
    
    @classmethod
    def correct_typos(cls, message: str) -> str:
        """Correct common typos in message"""
        corrected = message
        
        for typo, correction in cls.COMMON_TYPOS.items():
            # Use word boundaries to avoid partial matches
            import re
            pattern = r'\b' + re.escape(typo) + r'\b'
            corrected = re.sub(pattern, correction, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    @classmethod
    def infer_subject_from_context(cls, message: str, session) -> str:
        """
        Infer what the user is asking about based on context
        
        Returns: "cigar", "bourbon", or None
        """
        message_lower = message.lower()
        
        # Explicit mentions
        if any(w in message_lower for w in ["cigar", "cigars", "smoke", "stick"]):
            return "cigar"
        elif any(w in message_lower for w in ["bourbon", "whiskey", "bottle"]):
            return "bourbon"
        
        # Infer from session context
        if session.last_cigar_discussed and not session.last_bourbon_discussed:
            return "cigar"
        elif session.last_bourbon_discussed and not session.last_cigar_discussed:
            return "bourbon"
        
        # Check conversation history - what was discussed most recently?
        if session.conversation_history:
            last_turn = session.conversation_history[-1]["content"].lower()
            if "cigar" in last_turn:
                return "cigar"
            elif "bourbon" in last_turn:
                return "bourbon"
        
        return None
```

### 2.2 Use preprocessing in message handler

```python
def handle_message(self, session: SamSession, message: str) -> str:
    # STEP 1: Preprocess message
    corrected_message = MessagePreprocessor.correct_typos(message)
    
    if corrected_message != message:
        # Log the correction
        debugger.log_session_state(
            session.session_id,
            "typo_correction",
            {
                "original": message,
                "corrected": corrected_message
            }
        )
    
    # STEP 2: Infer subject if ambiguous
    subject = MessagePreprocessor.infer_subject_from_context(corrected_message, session)
    
    # STEP 3: If asking for "more options", use the inferred subject
    if "more" in corrected_message.lower() and ("option" in corrected_message.lower() or "recommendation" in corrected_message.lower()):
        if subject == "cigar":
            # Get the last cigar strength preference
            last_strength = session.last_cigar_info.get("strength") if session.last_cigar_info else None
            
            return self._get_more_cigar_recommendations(session, strength=last_strength)
        
        elif subject == "bourbon":
            return self._get_more_bourbon_recommendations(session)
    
    # Continue with normal processing...
    return self._process_message(session, corrected_message)
```

---

## STEP 3: Fix Intent Misclassification

### 3.1 Improve intent detection

**File: `sam_engine.py`**

```python
from cigar_retail_search import IntentClassifier

def handle_message(self, session: SamSession, message: str) -> str:
    # ... preprocessing from Step 2 ...
    
    # STEP 3: Classify intent BEFORE processing
    intent_result = IntentClassifier.detect_retail_search_intent(message, session)
    
    # Log intent detection
    debugger.log_session_state(
        session.session_id,
        "intent_detection",
        intent_result
    )
    
    # Route based on intent
    if intent_result["intent"] == "cigar_retail":
        return self._handle_cigar_retail_search(session, message)
    
    elif intent_result["intent"] == "bourbon_allocation":
        return self._handle_bourbon_allocation(session, message)
    
    # Continue with normal processing...
```

### 3.2 Add cigar retail handler

```python
def _handle_cigar_retail_search(self, session: SamSession, message: str) -> str:
    """Handle cigar retail search requests"""
    
    # Extract location from message
    location = self._extract_location(message)
    
    if not location:
        return """Hey there! I'd love to help you track down those cigars, but I need to know where you're located.

What's your ZIP code or city/state?

Once you tell me, I can point you toward some solid cigar shops in your area."""
    
    # Search for retailers
    retailers = self.cigar_retail_search.find_cigar_retailers(location=location)
    
    if retailers:
        response = f"Great! Here's where you can find {session.last_cigar_discussed or 'those cigars'}:\n\n"
        response += self.cigar_retail_search.format_retailers_for_response(retailers)
    else:
        response = f"""I'm having trouble finding cigar shops near {location}. 

Your best bets are:
• Check out local tobacco shops or cigar lounges
• Try online retailers like Famous Smoke Shop or Cigars International
• Call ahead to make sure they have {session.last_cigar_discussed or 'what you're looking for'}"""
    
    return response

def _extract_location(self, message: str) -> str:
    """Extract location from message"""
    import re
    
    # Check for ZIP code
    zip_match = re.search(r'\b\d{5}\b', message)
    if zip_match:
        return zip_match.group(0)
    
    # Check for city/state
    # Format: "City, ST" or "City, State"
    city_state_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2}|[A-Za-z\s]+)', message)
    if city_state_match:
        return city_state_match.group(0)
    
    # If user just says "near me", check if we have their location stored
    if "near me" in message.lower() and hasattr(self, 'user_location'):
        return self.user_location
    
    return None
```

---

## STEP 4: Fix Session Persistence

### 4.1 Verify session is being stored correctly

**File: `sam_engine.py`**

```python
class SamEngine:
    def __init__(self):
        self.sessions = {}  # In-memory storage
        # OR use Redis for production:
        # self.redis = redis.Redis(host='localhost', port=6379, db=0)
    
    def get_session(self, session_id: str) -> SamSession:
        """Get or create a session"""
        
        # Try to get from storage
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            debugger.log_session_state(
                session_id,
                "session_retrieved",
                {
                    "last_bourbon": session.last_bourbon_discussed,
                    "last_cigar": session.last_cigar_discussed,
                    "history_length": len(session.conversation_history)
                }
            )
            
            return session
        
        # Create new session
        session = SamSession(session_id=session_id)
        self.sessions[session_id] = session
        
        debugger.log_session_state(
            session_id,
            "session_created",
            {"status": "new_session"}
        )
        
        return session
    
    def save_session(self, session: SamSession):
        """Save session back to storage"""
        self.sessions[session.session_id] = session
        
        debugger.log_session_state(
            session.session_id,
            "session_saved",
            {
                "last_bourbon": session.last_bourbon_discussed,
                "last_cigar": session.last_cigar_discussed,
                "history_length": len(session.conversation_history)
            }
        )
```

### 4.2 Update session after EVERY message

```python
def handle_message(self, session: SamSession, message: str) -> str:
    # ... all processing ...
    
    response = self._generate_response(session, message)
    
    # CRITICAL: Update conversation history
    session.conversation_history.append({
        "role": "user",
        "content": message
    })
    session.conversation_history.append({
        "role": "assistant",
        "content": response
    })
    
    # CRITICAL: Save session
    self.save_session(session)
    
    return response
```

---

## STEP 5: Add Tests

### 5.1 Run the test suite

```bash
# Install pytest
pip install pytest requests

# Run unit tests
pytest test_failed_conversation.py -v

# Run integration tests (requires Sam API running)
pytest test_failed_conversation.py -m integration -v
```

### 5.2 Run deployment verification

```bash
# Verify your deployed API
python verify_deployment.py https://your-api-url.railway.app

# Or for local testing
python verify_deployment.py http://localhost:8000
```

---

## STEP 6: Deploy

### 6.1 Commit changes

```bash
git add sam_engine.py cigar_retail_search.py session_debugger.py
git commit -m "fix: context loss, intent classification, and session persistence"
git push origin main
```

### 6.2 Verify deployment

```bash
# Check Railway logs
railway logs

# Run verification script against production
python verify_deployment.py https://your-api-url.railway.app
```

---

## Testing the Fixes

After deployment, test the exact failed conversation:

```
You: whats a mid-tier, mild cigar
Sam: [provides Romeo y Julieta, etc.]

You: whats a mid-tier robust cigar
Sam: [provides Padron, Oliva, etc.]

You: give me mor robust optins
Sam: ✅ "You want more robust cigars? Here's some heavy hitters: CAO Brazilia..."
     (NOT "what are you looking for?")

You: where can i fid these cigars
Sam: ✅ "Where are you located? I can find cigar shops near you."
     (NOT "which specific ones?")

You: Oliva Serie V**
Sam: [provides Oliva varieties]

You: where can I find any of these near me
Sam: ✅ "What's your location? I'll find cigar shops for you."
     (NOT "Where should I look for allocation stores?")
```

---

## Success Metrics

✅ Context preserved across 5+ turns
✅ Typos don't break conversation
✅ "more options" correctly infers subject
✅ Cigar retail vs bourbon allocation correctly distinguished
✅ Session state persists between requests
✅ Debug endpoints show session state

---

## Rollback Plan

If something goes wrong:

```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Or restore previous Railway deployment
railway rollback
```
