# Sam Agent - Debugging & Fix Package

Complete diagnostic and fix package for the failed conversation issues in Sam.

## 📁 Files Included

### 🔍 Diagnostic Tools

1. **`quick_diagnostic.py`** - Fast diagnostic to identify what's broken
   - Tests the Romeo y Julieta bug
   - Checks context preservation
   - Validates intent classification
   - Verifies session state
   
   ```bash
   # Run locally
   python quick_diagnostic.py http://localhost:8000
   
   # Run against production
   python quick_diagnostic.py https://your-api.railway.app
   ```

2. **`verify_deployment.py`** - Comprehensive deployment verification
   - 4 detailed test scenarios
   - Validates all Phase 1 fixes
   - Checks debug endpoints
   
   ```bash
   python verify_deployment.py https://your-api.railway.app
   ```

3. **`session_debugger.py`** - Session state debugging middleware
   - Logs session state at every stage
   - Adds `/debug/session/{session_id}` endpoint
   - Tracks context decisions
   
   ```python
   # Add to your FastAPI app
   from session_debugger import add_debug_endpoints
   add_debug_endpoints(app)
   ```

### 🛠️ Implementation Files

4. **`cigar_retail_search.py`** - Cigar retailer search (separate from bourbon allocation)
   - Google Places API integration
   - Curated retailer database
   - IntentClassifier to distinguish cigar vs bourbon searches
   
   ```python
   from cigar_retail_search import CigarRetailSearch, IntentClassifier
   
   # Classify intent
   intent = IntentClassifier.detect_retail_search_intent(message, session)
   
   # Search for retailers
   retailers = search.find_cigar_retailers(location="19103")
   ```

5. **`test_failed_conversation.py`** - Test suite for the failed conversation
   - Unit tests for each failure mode
   - Integration tests that call real API
   - Pytest-based test harness
   
   ```bash
   # Run unit tests
   pytest test_failed_conversation.py -v
   
   # Run integration tests (requires running API)
   pytest test_failed_conversation.py -m integration
   ```

### 📖 Documentation

6. **`IMPLEMENTATION_GUIDE.md`** - Step-by-step implementation guide
   - 6 steps to fix all issues
   - Code examples for each fix
   - Testing procedures
   - Deployment checklist

7. **`README.md`** - This file

---

## 🚀 Quick Start

### Option 1: Just Diagnose (No Changes)

```bash
# Install dependencies
pip install requests

# Run quick diagnostic
python quick_diagnostic.py https://your-api.railway.app
```

This will tell you exactly what's broken.

### Option 2: Full Verification

```bash
# Run comprehensive tests
python verify_deployment.py https://your-api.railway.app
```

This runs 4 detailed scenarios and gives you a pass/fail for each.

### Option 3: Implement Fixes

```bash
# 1. Read the implementation guide
cat IMPLEMENTATION_GUIDE.md

# 2. Add session debugging to your API
# (Follow Step 1 in IMPLEMENTATION_GUIDE.md)

# 3. Add the fixes to sam_engine.py
# (Follow Steps 2-4 in IMPLEMENTATION_GUIDE.md)

# 4. Deploy
git add sam_engine.py cigar_retail_search.py session_debugger.py
git commit -m "fix: context loss, intent classification, session persistence"
git push origin main

# 5. Verify
python verify_deployment.py https://your-api.railway.app
```

---

## 🐛 Issues Identified

From the failed conversation screenshots, we identified:

### Issue 1: Context Loss
**Problem:**
```
User: "whats a mid-tier robust cigar"
Sam: [provides Padron, etc.]
User: "give me mor robust optins" (typo)
Sam: "Hey there! I'd love to help you out with some robust options, 
      but I need a bit more context..."
```

**Root Cause:** 
- Typo breaks parsing
- Session doesn't infer subject from context

**Fix:** 
- Add typo correction (Step 2.1)
- Implement context inference (Step 2.2)

### Issue 2: Intent Misclassification
**Problem:**
```
User: "where can I find any of these near me" (asking about CIGARS)
Sam: "Where should I look for allocation stores?" (bourbon allocation)
```

**Root Cause:**
- Intent classifier doesn't distinguish cigar retail from bourbon allocation
- "where to find" triggers bourbon allocation regardless of context

**Fix:**
- Implement IntentClassifier with subject detection (Step 3.1)
- Add separate cigar retail handler (Step 3.2)

### Issue 3: Session State Not Persisting
**Problem:**
- Context resets between turns
- `last_cigar_discussed` doesn't carry over

**Root Cause:**
- Session not being saved after each message
- Or session storage not working correctly

**Fix:**
- Verify session storage (Step 4.1)
- Save session after every message (Step 4.2)

---

## 🧪 Testing Strategy

### Level 1: Quick Diagnostic (2 minutes)
```bash
python quick_diagnostic.py https://your-api.railway.app
```
Tells you if the critical bugs are present.

### Level 2: Deployment Verification (5 minutes)
```bash
python verify_deployment.py https://your-api.railway.app
```
Runs 4 detailed scenarios with pass/fail.

### Level 3: Full Test Suite (10 minutes)
```bash
# Unit tests
pytest test_failed_conversation.py -v

# Integration tests
pytest test_failed_conversation.py -m integration -v
```
Comprehensive testing including edge cases.

### Level 4: Manual Testing
Follow the exact conversation that failed:

```
1. "whats a mid-tier, mild cigar"
2. "whats a mid-tier robust cigar"
3. "give me mor robust optins"          ← Should work without asking for clarification
4. "where can i fid these cigars"       ← Should offer cigar retailers, not bourbon
5. "Oliva Serie V**"
6. "where can I find any of these near me"  ← Should NOT mention allocation
```

---

## 📊 Success Criteria

✅ **Context Preservation**
- Sam remembers what was discussed 5+ turns ago
- Typos don't break conversation
- "more options" infers subject from context

✅ **Intent Classification**
- "where can I find cigars" → cigar retail search
- "where can I find bourbon" → bourbon allocation
- Context determines which type of search

✅ **Session Persistence**
- `last_cigar_discussed` survives between requests
- `last_bourbon_discussed` survives between requests
- Conversation history is maintained

✅ **Pronoun Resolution**
- "what pairs with it" correctly identifies what "it" refers to
- Pairing keywords help resolve ambiguous pronouns

---

## 🔧 Debug Endpoints

After adding `session_debugger.py`, you'll have these endpoints:

```bash
# Get debug info for a session
curl http://localhost:8000/debug/session/YOUR_SESSION_ID

# List all sessions with debug data
curl http://localhost:8000/debug/sessions

# Clear debug data
curl -X DELETE http://localhost:8000/debug/session/YOUR_SESSION_ID
```

These are invaluable for debugging session state issues.

---

## 📝 Implementation Checklist

- [ ] Run `quick_diagnostic.py` to identify issues
- [ ] Add `session_debugger.py` to your project
- [ ] Add debug endpoints to FastAPI app
- [ ] Implement typo correction (Step 2.1)
- [ ] Implement context inference (Step 2.2)
- [ ] Add `cigar_retail_search.py` to your project
- [ ] Implement intent classification (Step 3.1)
- [ ] Add cigar retail handler (Step 3.2)
- [ ] Verify session persistence (Step 4)
- [ ] Run `verify_deployment.py` locally
- [ ] Deploy to Railway
- [ ] Run `verify_deployment.py` against production
- [ ] Manual test the failed conversation
- [ ] Celebrate 🎉

---

## 🆘 Troubleshooting

### "API not reachable"
- Check Railway logs: `railway logs`
- Verify API URL is correct
- Test with curl: `curl https://your-api.railway.app/health`

### "Romeo bug still present"
- Check if `sam_engine.py` has pronoun resolution logic
- Verify session has `last_cigar_discussed` field
- Check debug endpoint: `/debug/session/{session_id}`

### "Context not preserved"
- Add logging to see if session is being saved
- Check if session storage is working (Redis/in-memory)
- Verify `save_session()` is called after each message

### "Intent misclassification"
- Add logging to see what intent was detected
- Check if `IntentClassifier` is being used
- Verify session context is available during classification

---

## 📚 Additional Resources

- **Session Summary Document** - Overview of all Phase 1 & 2 features
- **IMPLEMENTATION_GUIDE.md** - Detailed implementation steps
- **test_failed_conversation.py** - Test cases for validation

---

## 🎯 Next Steps

1. **Run diagnostics** to identify what's broken
2. **Follow implementation guide** to fix issues
3. **Test thoroughly** with provided test suite
4. **Deploy** and verify in production
5. **Move to Phase 2** (user learning system)

---

## ❓ Need Help?

If you're stuck:

1. Run `quick_diagnostic.py` to see what's failing
2. Check the debug endpoint: `/debug/session/{session_id}`
3. Review the implementation guide for that specific issue
4. Test locally before deploying

The implementation guide has code examples for every fix!
