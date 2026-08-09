import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.routes import router

load_dotenv()

app = FastAPI(
    title="Employee Support AI Agent API",
    description="Backend API for Enterprise HR & IT Support Assistant",
    version="1.0.0"
)

app.include_router(router, prefix="/api")

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "Employee Support AI Agent",
        "docs_url": "http://127.0.0.1:8000/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)