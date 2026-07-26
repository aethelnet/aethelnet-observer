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

# Import only LGNN routers
from routers import lgnn as lgnn_router
from routers import prophit_quant as pq_router
from routers import dashboard as dashboard_router
from lgnn.network.p2p_sync import p2p_router, start_p2p_hunter
from lgnn.network.bluetooth_mesh import start_bluetooth_mesh
from lgnn.living_loop import start_ecosystem_loop
from lgnn.p2p_gossip import start_p2p_gossip
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
        
        # LGNN WebSocket Broadcast
        if request.method in ["POST", "PUT", "DELETE"] and "/api/lgnn/" in request.url.path:
            try:
                from lgnn.websocket import manager
                asyncio.create_task(manager.broadcast("update"))
            except Exception as e:
                logger.error(f"Failed to broadcast update: {e}")
            
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
app.include_router(lgnn_router.router)
app.include_router(pq_router.router)
app.include_router(dashboard_router.router)
app.include_router(p2p_router)
app.include_router(auth_router.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Auratic Core...")
    start_ecosystem_loop()
    start_p2p_hunter()
    
    # Start the local Llama3 Ouroboros loop
    asyncio.create_task(ouroboros.run_forever())
    
    # Start Sovereign Rebalancer (Trading Service)
    from services.trading_service import run_trading_service
    asyncio.create_task(run_trading_service(), name="trading_core")
    
    # Start UDP Discovery
    try:
        from lgnn.network.udp_discovery import UDPDiscovery
        import socket
        node_id = f"auratic_node_{socket.gethostname()}"
        port = int(os.getenv("PORT", 8000))
        udp_discovery = UDPDiscovery(node_id=node_id, api_port=port)
        udp_discovery.start()
    except Exception as e:
        logger.warning(f"Could not start UDP Discovery: {e}")

    # Try to arm the Bluetooth Mesh and BLE Mesh for offline bridging
    try:
        start_bluetooth_mesh()
        
        from lgnn.network.ble_mesh import run_ble_mesh_daemon
        import threading
        ble_thread = threading.Thread(target=run_ble_mesh_daemon, daemon=True, name="BLE_Mesh_Thread")
        ble_thread.start()
    except Exception as e:
        logger.warning(f"Could not start Bluetooth/BLE Mesh: {e}")
    logger.info("🟢 [ONLINE] Sovereign Neural Engine Fully Engaged.")

@app.get("/health")
def health_check():
    return {"status": "operational", "system": "Auratic Prime v2.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
