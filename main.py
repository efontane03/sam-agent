from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.router import router as chat_router

app = FastAPI()

# Allow browser apps to call this API (for now, open to all origins).
# Later we can lock this down to your specific frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # in v1, keep simple
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
def home():
    return {"message": "SAM Agent is alive."}

