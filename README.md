# Uptime Sentinel

Uptime Sentinel is a self-hosted uptime monitoring platform.

The project is under active development. The current version provides a FastAPI backend, PostgreSQL persistence, monitor CRUD operations, health checks, database readiness checks, Alembic migrations, and a Docker Compose development environment.

## Current Features

- FastAPI REST API
- PostgreSQL database
- SQLAlchemy models and sessions
- Alembic database migrations
- Monitor CRUD API
- Liveness endpoint
- Database readiness endpoint
- Docker multi-stage build
- Docker Compose environment
- Persistent PostgreSQL volume
- Automated tests with Pytest

## Technology Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Pytest
- Docker
- Docker Compose

## Project Structure

```text
uptime-sentinel/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   └── monitors.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── infra/
│   └── docker/
│       ├── .env.example
│       └── docker-compose.yml
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install:

- Git
- Docker Engine or Docker Desktop
- Docker Compose

### Clone the Repository

```bash
git clone https://github.com/1Tsiupryk/uptime-sentintel.git
cd uptime-sentinel
```

### Configure the Environment

Create a local Docker environment file:

```bash
cp infra/docker/.env.example infra/docker/.env
```

Review `infra/docker/.env` and change the example password if necessary.

### Start the Application

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

Docker Compose will:

1. Start PostgreSQL.
2. Wait until PostgreSQL is healthy.
3. Run Alembic database migrations.
4. Start the FastAPI backend.

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## Health Endpoints

### Liveness

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Readiness

```bash
curl http://localhost:8000/ready
```

The readiness endpoint returns a successful response only when the backend can connect to PostgreSQL.

## Monitor API

Available operations:

- `POST /monitors` - Create a monitor
- `GET /monitors` - List monitors
- `GET /monitors/{monitor_id}` - Get a monitor
- `PATCH /monitors/{monitor_id}` - Update a monitor
- `DELETE /monitors/{monitor_id}` - Delete a monitor

Example:

```bash
curl -X POST http://localhost:8000/monitors -H "Content-Type: application/json" -d '{"name": "Example Website","url": "https://example.com"}'
```

List the created monitors:

```bash
curl http://localhost:8000/monitors
```

## Docker Commands

Start in the background:

```bash
docker compose -f infra/docker/docker-compose.yml up --build -d
```

View container status:

```bash
docker compose -f infra/docker/docker-compose.yml ps
```

View backend logs:

```bash
docker compose -f infra/docker/docker-compose.yml logs -f backend
```

Stop the application:

```bash
docker compose -f infra/docker/docker-compose.yml down
```

PostgreSQL data is stored in a named Docker volume and survives a normal restart.

To remove the containers and database volume:

```bash
docker compose -f infra/docker/docker-compose.yml down -v
```

> The `-v` option permanently deletes the local PostgreSQL data.

## Running Tests

Create and activate a virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies and run the tests:

```bash
python -m pip install -r requirements.txt
python -m pytest -v
```

## Roadmap

The further development of the project includes:

- Manual HTTP endpoint checks
- Check result history
- Background monitoring worker
- Redis integration
- Incident detection and recovery
- SSL certificate expiry checks
- Prometheus metrics
- Alert notifications
- Web dashboard
- CI pipeline
- Kubernetes deployment
- Ansible server bootstrap
- Operational runbooks

## Security Notes

- Secrets are provided through environment variables.
- Local `.env` files are excluded from Git.
- The backend container runs as a non-root user.
