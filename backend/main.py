import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from backend.routers.admin import router as admin_router

load_dotenv()

app = FastAPI(title="Post-Operative Voice Follow-Up Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "postop-voice-agent"}

# Static mounts for admin console
os.makedirs("console", exist_ok=True)
app.mount("/admin", StaticFiles(directory="console", html=True), name="admin")
