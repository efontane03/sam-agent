
from typing import Any, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class ChatRequest(BaseModel):
    mode: str                  # "chat" | "pairing" | "hunt"
    message: str               # user text from frontend
    advisor: str = "auto"      # "auto" | "sarn" | "mike"
    context: Optional[Dict[str, Any]] = None


app = FastAPI(
    title="Sam – Bourbon & Cigar Caddie API",
    version="1.0.0",
)

# Allow calls from your local file / any origin (dev-friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "sam-api"}


@app.post("/chat")
def chat_endpoint(payload: ChatRequest) -> Dict[str, Any]:
    """
    Mock implementation so we can prove:
    - Frontend → Railway → /chat works
    - All three modes return valid JSON
    """
    mode = payload.mode.lower().strip()

    # --- CHAT MODE SAMPLE ---
    if mode == "chat":
        return {
            "mode": "chat",
            "summary": f"CHAT sample reply for: {payload.message}",
            "key_points": [
                "This is a mock CHAT response from Sam.",
                "Once wiring is confirmed, we will plug in the real engine.",
            ],
            "next_step": "Try Pairing or Hunt mode to verify those layouts too.",
        }

    # --- PAIRING MODE SAMPLE ---
    if mode == "pairing":
        return {
            "mode": "pairing",
            "summary": f"PAIRING sample reply for: {payload.message}",
            "pairings": [
                {
                    "quality_tag": "Mid-Range",
                    "cigar_name": "Sample Toro",
                    "cigar_profile_short": "Medium body, cocoa and earth.",
                    "spirit_name": "Sample Bourbon",
                    "spirit_type": "Bourbon",
                    "spirit_profile_short": "Caramel, vanilla, gentle spice.",
                    "why_it_works_bullets": [
                        "Body of the cigar matches the proof of the bourbon.",
                        "Shared cocoa and vanilla notes keep it grounded.",
                        "Enough spice to stay interesting without fighting the smoke.",
                    ],
                    "allocation_status": "Regular shelf",
                    "allocation_note": "Easy to find in most decent shops.",
                    "hunt_tip_short": "Look for solid mid-shelf bottles, not hype labels.",
                    "suggested_use": "Easy Friday night pairing.",
                }
            ],
            "notes": "This is a mock PAIRING layout so we can style the frontend.",
            "next_step": "Ask for a real pairing vibe once the engine is wired back in.",
        }

    # --- HUNT MODE SAMPLE ---
    if mode == "hunt":
        return {
            "mode": "hunt",
            "summary": f"HUNT sample reply for: {payload.message}",
            "hunt_tips": [
                "Start with one or two independent shops with strong bourbon walls.",
                "Ask about email lists, raffles, or allocation drops—politely.",
                "Be a consistent customer, not just a unicorn hunter.",
            ],
            "next_step": "When you’re ready, name a specific bottle and we’ll target the hunt strategy.",
        }

    # --- FALLBACK ---
    return {
        "mode": "chat",
        "summary": f"Unknown mode '{payload.mode}', so I answered in CHAT style.",
        "key_points": [
            "Valid modes are: chat, pairing, hunt.",
        ],
        "next_step": "Try again with one of the supported modes.",
    }
