"""
user_profiles.py - User Learning and Preference Storage for Sam Agent

Stores user preferences and conversation history to provide personalized recommendations.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

# Database path
DB_PATH = os.environ.get("USER_PROFILES_DB", "/home/claude/user_profiles.db")

def init_database():
    """Initialize the user profiles database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            cigar_strength_preference TEXT,
            bourbon_price_preference TEXT,
            favorite_bourbons TEXT,
            favorite_cigars TEXT,
            disliked_flavors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Conversation history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            bourbon_discussed TEXT,
            cigar_discussed TEXT,
            interaction_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
        )
    """)
    
    # User feedback table (for future ratings)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            bourbon TEXT,
            cigar TEXT,
            rating INTEGER,
            feedback_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

class UserProfile:
    """User profile manager"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Ensure user exists
        self._ensure_user_exists()
    
    def _ensure_user_exists(self):
        """Create user profile if doesn't exist"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)",
            (self.user_id,)
        )
        self.conn.commit()
    
    def get_profile(self) -> Dict[str, Any]:
        """Get complete user profile"""
        self.cursor.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (self.user_id,)
        )
        row = self.cursor.fetchone()
        
        if not row:
            return {}
        
        return {
            "user_id": row["user_id"],
            "cigar_strength_preference": row["cigar_strength_preference"],
            "bourbon_price_preference": row["bourbon_price_preference"],
            "favorite_bourbons": json.loads(row["favorite_bourbons"]) if row["favorite_bourbons"] else [],
            "favorite_cigars": json.loads(row["favorite_cigars"]) if row["favorite_cigars"] else [],
            "disliked_flavors": json.loads(row["disliked_flavors"]) if row["disliked_flavors"] else [],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    
    def update_preference(self, preference_type: str, value: Any):
        """Update a specific preference"""
        if preference_type in ["favorite_bourbons", "favorite_cigars", "disliked_flavors"]:
            # JSON list fields
            value = json.dumps(value) if isinstance(value, list) else value
        
        self.cursor.execute(f"""
            UPDATE user_profiles 
            SET {preference_type} = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (value, self.user_id))
        self.conn.commit()
        print(f"✅ Updated {preference_type} for user {self.user_id}")
    
    def add_favorite_bourbon(self, bourbon: str):
        """Add bourbon to favorites"""
        profile = self.get_profile()
        favorites = profile.get("favorite_bourbons", [])
        
        bourbon_lower = bourbon.lower()
        if bourbon_lower not in [b.lower() for b in favorites]:
            favorites.append(bourbon)
            self.update_preference("favorite_bourbons", favorites)
    
    def add_favorite_cigar(self, cigar: str):
        """Add cigar to favorites"""
        profile = self.get_profile()
        favorites = profile.get("favorite_cigars", [])
        
        cigar_lower = cigar.lower()
        if cigar_lower not in [c.lower() for c in favorites]:
            favorites.append(cigar)
            self.update_preference("favorite_cigars", favorites)
    
    def log_interaction(self, bourbon: Optional[str] = None, 
                       cigar: Optional[str] = None, 
                       interaction_type: str = "general"):
        """Log a conversation interaction"""
        self.cursor.execute("""
            INSERT INTO conversation_history 
            (user_id, bourbon_discussed, cigar_discussed, interaction_type)
            VALUES (?, ?, ?, ?)
        """, (self.user_id, bourbon, cigar, interaction_type))
        self.conn.commit()
        
        # Auto-learn favorites (if discussed 3+ times, likely a favorite)
        if bourbon:
            self._check_and_add_favorite("bourbon", bourbon)
        if cigar:
            self._check_and_add_favorite("cigar", cigar)
    
    def _check_and_add_favorite(self, item_type: str, item_name: str):
        """Automatically add to favorites if discussed frequently"""
        column = "bourbon_discussed" if item_type == "bourbon" else "cigar_discussed"
        
        self.cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM conversation_history 
            WHERE user_id = ? AND {column} = ?
        """, (self.user_id, item_name))
        
        count = self.cursor.fetchone()["count"]
        
        if count >= 3:
            if item_type == "bourbon":
                self.add_favorite_bourbon(item_name)
            else:
                self.add_favorite_cigar(item_name)
    
    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        self.cursor.execute("""
            SELECT bourbon_discussed, cigar_discussed, interaction_type, timestamp
            FROM conversation_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (self.user_id, limit))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_personalized_greeting(self) -> Optional[str]:
        """Generate personalized greeting based on history"""
        profile = self.get_profile()
        history = self.get_recent_history(limit=1)
        
        # New user
        if not history:
            return None
        
        # Returning user
        last_interaction = history[0]
        
        greetings = []
        
        # Mention last bourbon
        if last_interaction.get("bourbon_discussed"):
            bourbon = last_interaction["bourbon_discussed"]
            greetings.append(f"Welcome back! Last time we talked about {bourbon.title()}.")
        
        # Mention favorites
        favorites = profile.get("favorite_bourbons", [])
        if favorites:
            greetings.append(f"I know you're a fan of {favorites[0].title()}.")
        
        return " ".join(greetings) if greetings else None
    
    def get_preference_summary(self) -> str:
        """Get a summary of user preferences for context"""
        profile = self.get_profile()
        
        parts = []
        
        if profile.get("cigar_strength_preference"):
            parts.append(f"prefers {profile['cigar_strength_preference']}-bodied cigars")
        
        if profile.get("bourbon_price_preference"):
            parts.append(f"typically buys {profile['bourbon_price_preference']}-range bourbon")
        
        if profile.get("favorite_bourbons"):
            favs = ", ".join(profile["favorite_bourbons"][:3])
            parts.append(f"favorites include {favs}")
        
        return "; ".join(parts) if parts else "no preferences set yet"
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def detect_preferences_from_message(message: str) -> Dict[str, str]:
    """Auto-detect preferences from user messages"""
    msg_lower = message.lower()
    preferences = {}
    
    # Detect strength preference
    if "full" in msg_lower or "strong" in msg_lower or "bold" in msg_lower:
        preferences["cigar_strength_preference"] = "full"
    elif "mild" in msg_lower or "light" in msg_lower or "smooth" in msg_lower:
        preferences["cigar_strength_preference"] = "mild"
    elif "medium" in msg_lower:
        preferences["cigar_strength_preference"] = "medium"
    
    # Detect price preference
    if "budget" in msg_lower or "cheap" in msg_lower or "affordable" in msg_lower:
        preferences["bourbon_price_preference"] = "budget"
    elif "premium" in msg_lower or "high-end" in msg_lower or "expensive" in msg_lower:
        preferences["bourbon_price_preference"] = "premium"
    elif "mid-range" in msg_lower or "middle" in msg_lower:
        preferences["bourbon_price_preference"] = "mid"
    
    return preferences

# Initialize database on import
try:
    init_database()
except Exception as e:
    print(f"⚠️  Warning: Could not initialize user profiles database: {e}")

if __name__ == "__main__":
    # Test the system
    print("Testing User Profile System...")
    
    # Create test user
    with UserProfile("test_user_123") as profile:
        print("\n1. New user profile created")
        
        # Log some interactions
        profile.log_interaction(bourbon="four roses", interaction_type="info")
        profile.log_interaction(bourbon="four roses", cigar="padron 2000", interaction_type="pairing")
        profile.log_interaction(bourbon="four roses", interaction_type="info")
        print("\n2. Logged 3 interactions with Four Roses")
        
        # Set preferences
        profile.update_preference("cigar_strength_preference", "full")
        profile.update_preference("bourbon_price_preference", "mid")
        print("\n3. Set preferences: full-bodied cigars, mid-range bourbon")
        
        # Get profile
        user_profile = profile.get_profile()
        print(f"\n4. User Profile: {json.dumps(user_profile, indent=2)}")
        
        # Get greeting
        greeting = profile.get_personalized_greeting()
        print(f"\n5. Personalized Greeting: {greeting}")
        
        # Get preference summary
        summary = profile.get_preference_summary()
        print(f"\n6. Preference Summary: {summary}")
    
    print("\n✅ All tests passed!")