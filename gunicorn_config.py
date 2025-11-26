# File: gunicorn_config.py
"""
Production Gunicorn configuration for Kuyala
Optimized for SSE and high concurrent connections
"""
import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker Processes
# For SSE, we use gevent workers which handle concurrent connections efficiently
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'gevent'  # Essential for SSE - handles concurrent streaming connections
worker_connections = 1000  # Max concurrent connections per worker
max_requests = 10000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 1000  # Add randomness to prevent all workers restarting at once

# Timeouts
# Long timeout for SSE connections (they stay open)
timeout = 300  # 5 minutes
graceful_timeout = 120  # Time to finish requests during shutdown
keepalive = 65  # Slightly longer than typical LB timeout of 60s

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')  # stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')   # stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Process Naming
proc_name = 'kuyala'

# Server Mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for faster worker spawning
preload_app = True

# Worker restart settings
max_requests = 10000
max_requests_jitter = 1000

# Server Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("=" * 80)
    server.log.info(f"Starting Kuyala Server")
    server.log.info(f"Binding to: {bind}")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info(f"Worker connections: {worker_connections}")
    server.log.info(f"Timeout: {timeout}s")
    server.log.info(f"Log level: {loglevel}")
    server.log.info("=" * 80)

def on_reload(server):
    """Called when reloading the configuration."""
    server.log.info("Configuration reloaded")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Kuyala server is ready to accept connections")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received ABRT signal")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # Don't log every request to avoid spam
    pass

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Don't log every request to avoid spam
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    server.log.info(f"Worker {worker.pid} exited")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Kuyala server shutting down...")