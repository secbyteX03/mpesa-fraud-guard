import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local modules
from model.database import Base, engine, get_db
from model.schemas import (
    TransactionCreate,
    TransactionResponse,
    RiskAssessmentResponse,
    TransactionWithRisk,
    HealthCheck,
    ErrorResponse
)
from model.fraud_detector import FraudDetector
from api.endpoints import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(
    title="MPESA Fraud Guard API",
    description="AI + Blockchain Fraud Prevention for Mobile Money in Kenya",
    version=os.getenv("APP_VERSION", "0.1.0"),
    middleware=middleware,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API routers
app.include_router(api_router, prefix="/api/v1", tags=["fraud-detection"])

# Initialize ML model
fraud_detector = FraudDetector()

# Create database tables
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Here you would typically load your trained model
        # For example: fraud_detector.load("path/to/model.joblib")
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["system"])
async def health_check():
    """Check the health of the API service"""
    return {
        "status": "healthy",
        "version": os.getenv("APP_VERSION", "0.1.0"),
        "timestamp": datetime.utcnow()
    }

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": getattr(exc, "error_code", None),
            "timestamp": datetime.utcnow().isoformat()
        },
    )

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to MPESA Fraud Guard API",
        "version": os.getenv("APP_VERSION", "0.1.0"),
        "docs": "/docs",
        "status": "operational"
    }

# Error handler for uncaught exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        },
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true",
        log_level="info"
    )
