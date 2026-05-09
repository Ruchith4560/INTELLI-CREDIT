from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api import auth, documents, analysis, cam, feedback
from app.database import engine, Base

load_dotenv()

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelli-Credit API",
    description="AI-Powered Credit Decisioning Platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["Analysis"])
app.include_router(cam.router,       prefix="/api/cam",       tags=["CAM Generator"])
app.include_router(feedback.router,  prefix="/api/feedback",  tags=["Feedback"])

# Directories
os.makedirs("uploads",          exist_ok=True)
os.makedirs("outputs",          exist_ok=True)
os.makedirs("models",           exist_ok=True)
os.makedirs("knowledge_base",   exist_ok=True)


@app.get("/")
def root():
    return {
        "message": "Intelli-Credit API v2.0 is running",
        "docs":    "/api/docs",
        "health":  "/health",
    }


@app.get("/health")
@app.get("/api/health")
def health():
    # Report which integrations are active
    import os
    return {
        "status": "healthy",
        "integrations": {
            "openai":    bool(os.getenv("OPENAI_API_KEY")),
            "serpapi":   bool(os.getenv("SERPAPI_KEY")),
            "newsapi":   bool(os.getenv("NEWS_API_KEY")),
            "ml_model":  os.path.exists("models/credit_model.pkl"),
            "rag":       os.path.exists("knowledge_base") and bool(
                [f for f in os.listdir("knowledge_base") if f.endswith(".pdf")]
            ),
        },
    }