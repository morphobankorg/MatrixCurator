---
description: Environment variables, Docker, and deployment configuration
globs: Dockerfile, docker-compose.yml, *.py, requirements.txt
---
# Configuration and Environment Standards

## 🎯 Directives
- ALWAYS follow the 12-Factor App methodology: store configuration that varies between environments in environment variables.
- ALWAYS implement "fail hard" logic for secrets in production. Raise `KeyError` if a required secret is missing when `DEBUG=False`.
- ALWAYS use a `requirements.txt` (or `pyproject.toml`/`uv.lock`) to explicitly declare production dependencies.
- ALWAYS separate development/testing dependencies from production dependencies.
- ALWAYS use Docker for containerization to ensure reproducible environments.
- ALWAYS use lightweight base images (e.g., `python:3.12-slim`).
- ALWAYS run applications as a nonroot user inside Docker containers.
- ALWAYS use bind mounts (`--mount type=bind`) for stateful data (like SQLite databases) and ensure host file permissions match the container's nonroot UID.
- ALWAYS use a production-ready WSGI/ASGI server (e.g., Gunicorn, Uvicorn) in Docker. NEVER use development servers (e.g., Django's `runserver`) in production.
- ALWAYS configure logging to output to the console (`StreamHandler`) so Docker can capture tracebacks.
- ALWAYS use `WhiteNoise` or a reverse proxy (Nginx) to serve static files in production.
- ALWAYS use declarative Infrastructure as Code (IaC) tools like Ansible for server provisioning and deployment.

## 📝 Examples

### ✅ DO
```python
import os

if "DJANGO_DEBUG_FALSE" in os.environ:
    DEBUG = False
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
    ALLOWED_HOSTS = [os.environ["DJANGO_ALLOWED_HOST"]]
else:
    DEBUG = True
    SECRET_KEY = "dev-secret-key"
    ALLOWED_HOSTS = []
```

### ❌ DON'T
```python
# Fails silently and runs insecurely in production
DEBUG = os.environ.get("DEBUG", False)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")