import os
import sys
import asyncio
import traceback
import warnings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Silence DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*Pandas4Warning.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load env
load_dotenv(os.path.join(project_root, '.env'))

# Setup logging
from core.logger import setup_global_logging, get_logger
setup_global_logging()
logger = get_logger("AuraticBackend")

# Import only core routers
from routers import prophit_quant as pq_router
from routers import dashboard as dashboard_router
from services.ouroboros import ouroboros
from routers import auth as auth_router

app = FastAPI(title="Auratic Systems Backend", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"[GLOBAL ERROR] Unhandled exception: {str(e)}")
        tb = traceback.format_exc()
        logger.error(tb)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal System Error", "detail": str(e)}
        )

# Mount Routers
app.include_router(pq_router.router)
app.include_router(dashboard_router.router)
app.include_router(auth_router.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Auratic Core Foundation...")
    
    # Start the local Llama3 Ouroboros loop
    asyncio.create_task(ouroboros.run_forever())
    
    # Start Sovereign Rebalancer (Trading Service)
    from services.trading_service import run_trading_service
    asyncio.create_task(run_trading_service(), name="trading_core")
    
    logger.info("🟢 [ONLINE] Sovereign Neural Engine Fully Engaged.")

@app.get("/health")
def health_check():
    return {"status": "operational", "system": "Auratic Prime v2.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 1421))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
