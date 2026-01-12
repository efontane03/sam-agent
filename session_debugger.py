"""
Session State Debugging Module
Add this to your FastAPI app to debug session state issues
"""

from fastapi import FastAPI, Request
from typing import Dict, Any
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionStateDebugger:
    """
    Middleware to log and debug session state throughout the request lifecycle
    """
    
    def __init__(self):
        self.session_snapshots = {}
    
    def log_session_state(self, session_id: str, stage: str, session_data: Dict[str, Any]):
        """
        Log session state at different stages
        
        Args:
            session_id: Unique session identifier
            stage: Stage of request (e.g., "start", "after_parse", "before_response")
            session_data: Current session data to log
        """
        if session_id not in self.session_snapshots:
            self.session_snapshots[session_id] = []
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "data": session_data
        }
        
        self.session_snapshots[session_id].append(snapshot)
        
        # Log to console
        logger.info(f"""
==================================================
SESSION DEBUG - {stage}
Session ID: {session_id}
Timestamp: {snapshot['timestamp']}
==================================================
{json.dumps(session_data, indent=2)}
==================================================
        """)
    
    def get_session_history(self, session_id: str) -> list:
        """Get all snapshots for a session"""
        return self.session_snapshots.get(session_id, [])
    
    def clear_session_history(self, session_id: str):
        """Clear history for a session"""
        if session_id in self.session_snapshots:
            del self.session_snapshots[session_id]


# Global debugger instance
debugger = SessionStateDebugger()


def add_debug_endpoints(app: FastAPI):
    """
    Add debug endpoints to your FastAPI app
    
    Usage:
        from session_debugger import add_debug_endpoints
        add_debug_endpoints(app)
    """
    
    @app.get("/debug/session/{session_id}")
    async def get_session_debug(session_id: str):
        """Get debug history for a session"""
        history = debugger.get_session_history(session_id)
        
        if not history:
            return {
                "session_id": session_id,
                "message": "No debug data found for this session",
                "snapshots": []
            }
        
        return {
            "session_id": session_id,
            "total_snapshots": len(history),
            "snapshots": history
        }
    
    @app.get("/debug/sessions")
    async def list_debug_sessions():
        """List all sessions with debug data"""
        return {
            "sessions": list(debugger.session_snapshots.keys()),
            "total": len(debugger.session_snapshots)
        }
    
    @app.delete("/debug/session/{session_id}")
    async def clear_session_debug(session_id: str):
        """Clear debug data for a session"""
        debugger.clear_session_history(session_id)
        return {"message": f"Cleared debug data for session {session_id}"}


# Decorator to auto-log session state
def debug_session_state(stage: str):
    """
    Decorator to automatically log session state at different stages
    
    Usage:
        @debug_session_state("before_pairing_search")
        def get_pairing_recommendations(session):
            # Your code here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to find session object in args
            session = None
            session_id = None
            
            for arg in args:
                if hasattr(arg, 'session_id'):
                    session = arg
                    session_id = arg.session_id
                    break
            
            # If session found, log its state
            if session:
                session_data = {
                    "session_id": session_id,
                    "last_bourbon_discussed": getattr(session, 'last_bourbon_discussed', None),
                    "last_bourbon_info": getattr(session, 'last_bourbon_info', None),
                    "last_cigar_discussed": getattr(session, 'last_cigar_discussed', None),
                    "last_cigar_info": getattr(session, 'last_cigar_info', None),
                    "conversation_history": getattr(session, 'conversation_history', [])[-3:],  # Last 3 turns
                }
                
                debugger.log_session_state(session_id, stage, session_data)
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log state after execution if session was found
            if session:
                session_data_after = {
                    "session_id": session_id,
                    "last_bourbon_discussed": getattr(session, 'last_bourbon_discussed', None),
                    "last_bourbon_info": getattr(session, 'last_bourbon_info', None),
                    "last_cigar_discussed": getattr(session, 'last_cigar_discussed', None),
                    "last_cigar_info": getattr(session, 'last_cigar_info', None),
                }
                
                debugger.log_session_state(session_id, f"{stage}_after", session_data_after)
            
            return result
        
        return wrapper
    return decorator


# Example usage in your sam_engine.py:
"""
# Import at the top of sam_engine.py
from session_debugger import debug_session_state, debugger

# In your message handler
@debug_session_state("message_received")
def handle_message(session, message):
    # Log at start of request
    debugger.log_session_state(
        session.session_id,
        "message_start",
        {
            "user_message": message,
            "last_bourbon": session.last_bourbon_discussed,
            "last_cigar": session.last_cigar_discussed
        }
    )
    
    # Your existing logic
    response = process_message(session, message)
    
    # Log before returning
    debugger.log_session_state(
        session.session_id,
        "message_complete",
        {
            "response_preview": response[:200],
            "last_bourbon": session.last_bourbon_discussed,
            "last_cigar": session.last_cigar_discussed
        }
    )
    
    return response

# In your FastAPI app initialization (api_handler.py)
from session_debugger import add_debug_endpoints

app = FastAPI()
add_debug_endpoints(app)  # This adds the /debug/session endpoints
"""


# Manual logging helper
def log_context_decision(session_id: str, user_message: str, decision: Dict[str, Any]):
    """
    Log context resolution decisions for debugging
    
    Usage:
        log_context_decision(
            session.session_id,
            message,
            {
                "detected_pronoun": "it",
                "context_type": "cigar",
                "resolved_to": "Romeo y Julieta",
                "reasoning": "User asked 'what bourbon pairs with it' - detected pairing keywords"
            }
        )
    """
    logger.info(f"""
==================================================
CONTEXT RESOLUTION DECISION
Session ID: {session_id}
User Message: "{user_message}"
==================================================
{json.dumps(decision, indent=2)}
==================================================
    """)
    
    # Also save to debugger
    debugger.log_session_state(
        session_id,
        "context_resolution",
        {
            "user_message": user_message,
            "decision": decision
        }
    )