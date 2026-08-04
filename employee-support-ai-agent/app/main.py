import uvicorn
from fastapi import FastAPI
from app.api.routes import router
from app.database.database import init_db, seed_db

app = FastAPI(title="Enterprise HR & IT Support AI Agent")

# Register API Router
app.include_router(router, prefix="/api")

@app.on_event("startup")
def on_startup():
    print("🚀 Initializing Enterprise SQLite Database...")
    init_db()
    seed_db()

@app.get("/")
def root():
    return {"status": "Online", "mode": "Direct MCP Execution Engine"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)