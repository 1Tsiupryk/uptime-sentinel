# Uptime Sentinel

Uptime Sentinel is a self-hosted uptime monitoring platform for tracking HTTP endpoints. It provides scheduled and on-demand checks, stores check history, and exposes the results through a web dashboard and REST API.

## Current Features

- Create, view, update, pause, and delete HTTP monitors
- Configure the expected HTTP status code, check interval, and request timeout
- Trigger checks manually from the dashboard or API
- Store status, response code, latency, error details, and check time
- Run scheduled checks in background workers
- Coordinate multiple workers with Redis distributed locks
- View recent check history
- PostgreSQL persistence with Alembic migrations
- Liveness and database readiness endpoints
- Container health checks and non-root application containers

## Architecture

```text
Browser
   |
   v
Frontend (React + Nginx, port 3000)
   |
   | /api
   v
Backend (FastAPI, port 8000) -----> PostgreSQL
                                          ^
                                          |
Background worker ------------------------+
   |
   v
Redis (distributed monitor locks)
```

The backend handles monitor management and on-demand checks. The worker periodically finds due monitors and performs scheduled checks. Redis prevents two or more worker replicas from checking the same monitor at the same time.

## Technology Stack

### Backend

- Python 3.13
- FastAPI and Uvicorn
- SQLAlchemy and Alembic
- PostgreSQL
- Redis
- Pytest

### Frontend

- React 19
- TypeScript
- Vite
- Nginx

### Infrastructure

- Docker
- Docker Compose

## Project Structure

```text
uptime-sentintel/
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/                 # Health, monitor, and check routes
│   │   ├── services/            # HTTP checker, persistence, Redis locks
│   │   ├── worker/              # Scheduled check worker
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── redis_client.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── test/
│   │   ├── types/
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── infra/
│   └── docker/
│       ├── .env.example
│       └── docker-compose.yml
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Git
- Docker Engine or Docker Desktop
- Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/1Tsiupryk/uptime-sentinel.git
cd uptime-sentinel
```

### 2. Configure environment variables

```bash
cp infra/docker/.env.example infra/docker/.env
```

For local development the defaults work as provided. Change `POSTGRES_PASSWORD` before using the project outside a local environment.

### 3. Start the complete stack

```bash
docker compose -f infra/docker/docker-compose.yml up --build -d
```

Compose starts PostgreSQL, Redis, the FastAPI backend, the background worker, and the frontend. The backend container applies Alembic migrations before starting the API.

### 4. Open the application

- Dashboard: <http://localhost:3000>
- API documentation: <http://localhost:8000/docs>

Check the container status:

```bash
docker compose -f infra/docker/docker-compose.yml ps
```

## API

### Health endpoints

- `GET /health` - Backend liveness check
- `GET /ready` - PostgreSQL readiness check

### Monitor endpoints

- `POST /monitors` - Create a monitor
- `GET /monitors` - List all monitors
- `GET /monitors/{monitor_id}` - Get one monitor
- `PATCH /monitors/{monitor_id}` - Update or pause a monitor
- `DELETE /monitors/{monitor_id}` - Delete a monitor and its check history
- `POST /monitors/{monitor_id}/check` - Run an on-demand check
- `GET /monitors/{monitor_id}/checks` - Get the monitor's check history

## Useful Docker Commands

View logs:

```bash
docker compose -f infra/docker/docker-compose.yml logs -f
```

View only API or worker logs:

```bash
docker compose -f infra/docker/docker-compose.yml logs -f backend worker
```

Rebuild and restart the stack:

```bash
docker compose -f infra/docker/docker-compose.yml up --build -d
```

Stop the stack while preserving PostgreSQL data:

```bash
docker compose -f infra/docker/docker-compose.yml down
```

Delete the stack and its PostgreSQL volume:

```bash
docker compose -f infra/docker/docker-compose.yml down -v
```

> `down -v` permanently removes the local database volume and all stored monitors and check results.

## Environment Variables

The Docker stack is configured through `infra/docker/.env`.

- `POSTGRES_*` - PostgreSQL connection and database credentials
- `WORKER_POLL_INTERVAL_SECONDS` - How often the worker searches for due monitors
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` - Redis connection settings
- `REDIS_SOCKET_TIMEOUT_SECONDS` - Redis operation timeout
- `REDIS_LOCK_TIMEOUT_SECONDS` - Maximum lifetime of a monitor lock
- `CORS_ALLOWED_ORIGINS` - Origins allowed to call the API directly

The frontend Docker image uses `/api` by default and Nginx proxies those requests to the backend. For local Vite development, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL` to the backend URL.

## Roadmap

- Incident detection and recovery tracking
- Prometheus metrics and Grafana dashboards
- CI pipeline
- Kubernetes deployment
- Ansible server bootstrap
- Operational runbooks

## Security Notes

- Secrets are provided through environment variables.
- The backend container runs as a non-root user.
- The frontend uses the unprivileged Nginx image and listens on port `8080` inside the container.
- PostgreSQL is exposed only on the host loopback interface in the local Compose setup.
