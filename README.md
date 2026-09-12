# Uptime Sentinel
[![CI](https://github.com/1Tsiupryk/uptime-sentinel/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/1Tsiupryk/uptime-sentinel/actions/workflows/ci.yml)

Uptime Sentinel is a self-hosted uptime monitoring platform for tracking HTTP endpoints. It provides scheduled and on-demand checks, stores check history, and exposes the results through a web dashboard and REST API.

## Current Features

- Configure and manage HTTP monitors with custom status codes, intervals, and timeouts
- Run on-demand and scheduled checks using horizontally scalable background workers
- Prevent duplicate checks across worker replicas with Redis distributed locks
- Store check history and automatically track incidents from outage through recovery
- Explore live monitor status, check history, and incidents through the React dashboard
- Persist application data in PostgreSQL with versioned Alembic migrations
- Export application and worker metrics to Prometheus with a provisioned Grafana dashboard
- Deploy the complete stack with Docker Compose or Kubernetes using staged migration and application rollouts
- Route Kubernetes traffic through Traefik, Gateway API and multiple application replicas
- Protect Kubernetes workloads with restricted Pod Security, non-root containers, dropped capabilities, and default-deny NetworkPolicies

## Architecture

```text
Browser
   |
   v
Frontend (React + Nginx)
   |
   | /api
   v
Backend (FastAPI) -----> PostgreSQL
   |                            ^
   | /metrics                   |
   v                            |
Prometheus <------ Background workers
   |
   v
Grafana
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
- Kubernetes
- Kind
- Helm
- Traefik Gateway API
- Prometheus Operator
- NetworkPolicy

## Project Structure

```text
uptime-sentinel/
├── .github/
│   └── workflows/
│       └── ci.yml                         # Tests, builds, and infrastructure validation
├── backend/
│   ├── alembic/
│   │   └── versions/                      # Database migrations
│   ├── app/
│   │   ├── api/                           # Health, metrics, monitors, checks, incidents
│   │   ├── services/                      # Checker, incidents, locks, and metrics logic
│   │   ├── worker/                        # Scheduled check worker
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── metrics.py
│   │   ├── models.py
│   │   ├── redis_client.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                           # Backend API client
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── test/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── infra/
│   ├── docker/
│   │   ├── .env.example
│   │   └── docker-compose.yml
│   ├── grafana/
│   │   ├── dashboards/                    # Provisioned Uptime Sentinel dashboard
│   │   └── provisioning/                  # Docker Compose provisioning
│   ├── prometheus/
│   │   └── prometheus.yml                 # Docker Compose scrape configuration
│   └── kubernetes/
│       ├── base/
│       │   ├── application/               # Backend, worker, frontend, and Gateway
│       │   ├── infrastructure/            # Namespace, PostgreSQL, Redis, and policies
│       │   └── migration/                 # Alembic migration Job
│       ├── monitoring/                    # Helm values, ServiceMonitor, and PodMonitor
│       ├── overlays/
│       │   └── local/                     # Local Kind image and secret configuration
│       └── traefik/
│           └── values.yml
├── scripts/
│   ├── deploy-local.sh                    # Staged Kubernetes application deployment
│   └── deploy-monitoring.sh               # Prometheus and Grafana deployment
├── .gitignore
├── pyrefly.toml
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

## Kubernetes Deployment

### Prerequisites

- Docker
- kubectl
- Kind
- Helm

### 1. Create a local cluster

```bash
kind create cluster --name uptime-sentinel
```

### 2. Install Gateway API and Traefik

```bash
kubectl apply --server-side -f \
  https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.1/standard-install.yaml

helm repo add traefik https://traefik.github.io/charts --force-update

helm upgrade --install traefik traefik/traefik \
  --version 41.5.0 \
  --namespace traefik \
  --create-namespace \
  --values infra/kubernetes/traefik/values.yml \
  --wait \
  --timeout 5m
```

### 3. Configure the application

```bash
cp infra/kubernetes/overlays/local/infrastructure/.env.example \
  infra/kubernetes/overlays/local/infrastructure/.env
```

Review the generated environment file and replace local development credentials when necessary.

### 4. Build and load application images

```bash
docker build -t uptime-sentinel-backend:local ./backend
docker build -t uptime-sentinel-frontend:local ./frontend

kind load docker-image uptime-sentinel-backend:local \
  --name uptime-sentinel

kind load docker-image uptime-sentinel-frontend:local \
  --name uptime-sentinel
```

### 5. Deploy the application

```bash
./scripts/deploy-local.sh
```

The script deploys PostgreSQL and Redis, runs Alembic migrations, and then rolls out the backend, workers, frontend, Gateway, and HTTPRoute.

Access the application through Traefik:

```bash
kubectl port-forward -n traefik service/traefik 8080:80
```

Open <http://localhost:8080>.

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

### Kubernetes monitoring

Deploy Prometheus Operator, Prometheus, Grafana, application monitors, and the provisioned dashboard:

```bash
./scripts/deploy-monitoring.sh
```

Access Prometheus:

```bash
kubectl port-forward -n monitoring \
  service/monitoring-kube-prometheus-prometheus 9090:9090
```

Access Grafana:

```bash
kubectl port-forward -n monitoring \
  service/monitoring-grafana 3002:80
```

Prometheus discovers backend replicas through a `ServiceMonitor` and worker replicas through a `PodMonitor`. Grafana loads the `Uptime Sentinel Overview` dashboard from a generated ConfigMap.

The default Grafana username is `admin`. Retrieve the generated password:

```bash
kubectl get secret monitoring-grafana -n monitoring \
  -o jsonpath='{.data.admin-password}' | base64 --decode
```

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

## Continuous Integration

GitHub Actions runs the following checks on every push and pull request to `main`:

- Backend tests with Pytest
- Frontend linting, tests, and production build
- Backend and frontend Docker image builds
- Docker Compose configuration validation
- Kubernetes Kustomize manifest validation
- Traefik and kube-prometheus-stack Helm rendering
- Local deployment script syntax validation

## Roadmap

- Ansible server bootstrap
- Operational runbooks

## Security Notes

- Secrets are provided through environment variables.
- The backend container runs as a non-root user.
- The frontend uses the unprivileged Nginx image and listens on port `8080` inside the container.
- PostgreSQL is exposed only on the host loopback interface in the local Compose setup.
- Uptime Sentinel application workloads run as non-root users with dropped Linux capabilities and privilege escalation disabled.
- The application namespace uses Kubernetes Pod Security admission controls.
- Default-deny NetworkPolicies restrict traffic between the frontend, backend, workers, PostgreSQL, Redis, Traefik, and Prometheus.
- Kubernetes ServiceAccount token mounting is disabled where it is not required.
