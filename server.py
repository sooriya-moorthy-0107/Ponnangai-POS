import os
import sys
import logging
import time

# Enforce Indian Standard Time (IST) on AppSail container environment
os.environ["TZ"] = "Asia/Kolkata"
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

# Ensure local lib directory is in sys.path for Catalyst AppSail dependencies
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for lib_cand in [os.path.join(BASE_DIR, "lib"), os.path.abspath("lib")]:
    if os.path.isdir(lib_cand) and lib_cand not in sys.path:
        sys.path.insert(0, lib_cand)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

if __name__ == "__main__":
    try:
        raw_port = os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT") or os.environ.get("PORT") or "8000"
        try:
            port = int(raw_port)
        except Exception:
            port = 8000
        
        logger.info(f"Starting POS server on 0.0.0.0:{port}...")
        import uvicorn
        from main import app
        # forwarded_allow_ips='*' is essential for reverse-proxy architectures like Zoho Catalyst
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", forwarded_allow_ips="*")
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        logger.error(f"CRITICAL: Failed to launch POS server: {e}\n{trace}")
        print(f"CRITICAL: Failed to launch POS server: {e}\n{trace}", file=sys.stderr, flush=True)
        sys.exit(1)
