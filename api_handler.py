"""
api_handler.py - FastAPI endpoint with User ID support

Add this to your backend (main.py or create new file)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

# Your existing imports
from sam_engine import sam_engine, SamSession

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_state: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: Dict[str, Any]
    user_id: str

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint with user ID support
    
    Example request:
    {
        "message": "tell me about four roses",
        "user_id": "user_1234567890_abc123",
        "session_state": {}
    }
    """
    
    # Generate user ID if not provided
    user_id = request.user_id
    if not user_id:
        user_id = f"anonymous_{uuid.uuid4()}"
        print(f"⚠️ No user_id provided, generated: {user_id}")
    
    try:
        # Create session with user ID
        session = SamSession(user_id=user_id)
        
        # Load existing session state if provided
        if request.session_state:
            session.context = request.session_state.get("context", {})
            session.last_bourbon_discussed = request.session_state.get("last_bourbon_discussed")
            session.last_cigar_discussed = request.session_state.get("last_cigar_discussed")
        
        # Process message
        response = sam_engine(request.message, session)
        
        return ChatResponse(
            response=response,
            user_id=user_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/profile")
def get_user_profile(user_id: str):
    """
    Get user profile data
    
    Example: GET /user/user_1234567890_abc123/profile
    """
    try:
        from user_profiles import UserProfile
        
        with UserProfile(user_id) as profile:
            return {
                "profile": profile.get_profile(),
                "recent_history": profile.get_recent_history(limit=10),
                "preference_summary": profile.get_preference_summary()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/user/{user_id}/profile")
def delete_user_profile(user_id: str):
    """
    Delete user profile (forget me)
    
    Example: DELETE /user/user_1234567890_abc123/profile
    """
    try:
        import sqlite3
        from user_profiles import DB_PATH
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Delete from all tables
        cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM conversation_history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_feedback WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return {"status": "deleted", "user_id": user_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sam-agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)