# Uptime Sentinel

Uptime Sentinel is a self-hosted uptime monitoring platform for tracking HTTP endpoints. It provides scheduled and on-demand checks, stores check history, and exposes the results through a web dashboard and REST API.

## Current Features

- Manage HTTP monitors with configurable status codes, intervals, and timeouts
- Run on-demand and scheduled checks with detailed result history
- Scale background workers safely with Redis distributed locks
- Track incidents automatically from outage detection through recovery
- Prevent duplicate incidents and record duration, related checks, and lifecycle events
- Explore live-updating monitor, check, and incident data in the web dashboard
- Persist application data in PostgreSQL with Alembic migrations
- Run a containerized stack with health checks, readiness endpoints, and non-root containers
- Export Prometheus metrics and visualize system health through a provisioned Grafana dashboard

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
   |                                      ^
   | /metrics                             |
   v                                      |
Prometheus <------ Background workers ----+
   |
   v
Grafana (port 3001)
```

The backend handles monitor management and on-demand checks. The worker periodically finds due monitors and performs scheduled checks. Redis prevents two or more worker replicas from checking the same monitor at the same time.

## Incident Lifecycle

An incident is automatically opened when a monitor check returns a `down` result. Consecutive failed checks remain associated with the same active incident.

When a later check returns `up`, the active incident is resolved. Each incident stores its opening and closing check references, start time, resolution time, and calculated duration.

The dashboard polls the API every 10 seconds to refresh active incident counters, monitor badges, and incident history.

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
- Prometheus
- Grafana

## Project Structure

```text
uptime-sentintel/
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/                 # Health, metrics, monitor, and check routes
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
│   ├── docker/
│   │   └── docker-compose.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       │   └── uptime-sentinel-overview.json
│       └── provisioning/
│           ├── dashboards/
│           └── datasources/
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

### Incident endpoints

- `GET /incidents` - List all incidents
- `GET /incidents?status=open` - List active incidents
- `GET /incidents?status=resolved` - List resolved incidents
- `GET /incidents/{incident_id}` - Get incident details
- `GET /monitors/{monitor_id}/incidents` - List incidents for a specific monitor

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

## Observability

The backend and background workers expose Prometheus metrics for HTTP checks, latency, monitor status, and incident lifecycle events.

Available services:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Backend metrics: `http://localhost:8000/metrics`

The Grafana Prometheus data source and the `Uptime Sentinel Overview` dashboard are provisioned automatically when the stack starts.

Exported metrics include:

- `uptime_sentinel_checks_total` — completed checks grouped by monitor and status
- `uptime_sentinel_check_latency_seconds` — check latency histogram
- `uptime_sentinel_incident_events_total` — opened and resolved incident events
- `uptime_sentinel_monitor_up` — latest known status of enabled monitors

Prometheus discovers all worker replicas through Docker DNS and scrapes their metrics independently.

## Environment Variables

The Docker stack is configured through `infra/docker/.env`.

- `POSTGRES_*` - PostgreSQL connection and database credentials
- `WORKER_POLL_INTERVAL_SECONDS` - How often the worker searches for due monitors
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` - Redis connection settings
- `REDIS_SOCKET_TIMEOUT_SECONDS` - Redis operation timeout
- `REDIS_LOCK_TIMEOUT_SECONDS` - Maximum lifetime of a monitor lock
- `CORS_ALLOWED_ORIGINS` - Origins allowed to call the API directly
- `WORKER_METRICS_PORT` - Internal port used to expose worker Prometheus metrics
- `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD` - Grafana administrator credentials

The frontend Docker image uses `/api` by default and Nginx proxies those requests to the backend. For local Vite development, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL` to the backend URL.

## Roadmap

- CI pipeline
- Kubernetes deployment
- Ansible server bootstrap
- Operational runbooks

## Security Notes

- Secrets are provided through environment variables.
- The backend container runs as a non-root user.
- The frontend uses the unprivileged Nginx image and listens on port `8080` inside the container.
- PostgreSQL is exposed only on the host loopback interface in the local Compose setup.
