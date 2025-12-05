from fastapi import FastAPI
from agent.router import router as chat_router

app = FastAPI()

app.include_router(chat_router)

@app.get("/")
def home():
    return {"message": "SAM Agent is alive."}
