import os
import sys
import logging

# Ensure local lib directory is in sys.path for Catalyst AppSail dependencies
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(BASE_DIR, "lib")
if os.path.isdir(LIB_DIR) and LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

if __name__ == "__main__":
    raw_port = os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT") or os.environ.get("PORT") or "8000"
    try:
        port = int(raw_port)
    except Exception:
        port = 8000
    
    logger.info(f"Starting POS server on 0.0.0.0:{port}...")
    import uvicorn
    # forwarded_allow_ips='*' is essential for reverse-proxy architectures like Zoho Catalyst
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info", forwarded_allow_ips="*")
