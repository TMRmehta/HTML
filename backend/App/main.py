# Library Imports
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = ""

# Local Imports
from Agents.routes.agent_apis import router as agent
from CustomTools.routes.chats_api import router as chats
from App.config import settings
from App.routes import auth
from App import schemas as app_schemas
from App import models as app_models
from Database import models as db_models
from Database.database import SessionLocal, engine

# Create database tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    db_models.Base.metadata.create_all(bind=engine)
    app_models.Base.metadata.create_all(bind=engine)
    yield

# Create FastAPI app
app = FastAPI(
    title="Oncosight.AI API",
    description="Medical AI platform for cancer research and patient care",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,
)

base = "/api/v1"
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix=base)
app.include_router(agent, prefix=base)
app.include_router(chats, prefix=base)



# Handle preflight OPTIONS requests


@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle preflight OPTIONS requests for all paths."""
    return {"message": "OK"}

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Oncosight.AI API is running"}

# Root endpoint


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Oncosight.AI API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Database dependency


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
