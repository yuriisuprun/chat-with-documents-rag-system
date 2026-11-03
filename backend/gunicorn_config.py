"""
Gunicorn configuration for production deployment (2026 best practices).

2026 Pattern: Gunicorn process manager + multiple Uvicorn workers
- Better concurrency handling
- Graceful reloads
- Worker process management
"""

import multiprocessing
import os

# Server socket
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)

# Process naming
proc_name = "rag-system"

# Reload on code changes (development only)
reload = os.getenv("ENVIRONMENT", "production") == "development"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
umask = 0
user = None
group = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Gunicorn starting with {workers} workers")

def when_ready(server):
    """Called just after the server is started."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Gunicorn ready. Spawning workers. (bind={bind})")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Gunicorn exiting")
