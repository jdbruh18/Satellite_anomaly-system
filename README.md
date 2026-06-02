# Satellite Telemetry Anomaly System

Modular async FastAPI service for ingesting satellite telemetry JSON, validating it, persisting it in PostgreSQL, and scoring new points with an Isolation Forest anomaly detector.

The detector trains on recent telemetry that was previously classified as normal for the same satellite, then reports anomaly categories such as `temperature_spike`, `power_drop`, `signal_instability`, and `fuel_anomaly`.

## Architecture

```text
app/
  ai/           AI model protocols and anomaly engines
  api/          FastAPI routers and route handlers
  core/         configuration and structured logging
  db/           async SQLAlchemy engine, sessions, repositories
  events/       domain event publishers
  integrations/ external telemetry feed clients
  models/       database models
  observability/ runtime metrics and counters
  schemas/      Pydantic request and response models
  services/     anomaly and ingestion business logic
  simulator/    telemetry generator
  workers/      batch and background job entry points
scripts/        helper scripts
tests/          focused unit tests
```

## Run With Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.
PostgreSQL will be available inside Docker as `postgres:5432` and on the host at `localhost:5432`.

Check container health:

```bash
docker compose ps
curl http://localhost:8000/api/v1/health/db
```

Stop the stack:

```bash
docker compose down
```

Remove the PostgreSQL data volume when you need a fresh telemetry schema:

```bash
docker compose down -v
```

Useful endpoints:

- `GET /api/v1/health`
- `GET /api/v1/health/db`
- `POST /api/v1/telemetry`
- `POST /api/v1/telemetry/simulate`
- `GET /api/v1/telemetry`
- `GET /api/v1/anomalies`
- `GET /api/v1/metrics`

## Example Ingest

```bash
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "satellite_id": "SAT-001",
    "sequence": 1,
    "battery_voltage": 27.2,
    "solar_output": 84.5,
    "cpu_temperature": 43.1,
    "fuel_level": 70.8,
    "signal_strength": -68.4,
    "orientation_pitch": 0.7,
    "orientation_yaw": -1.2
  }'
```

## Generate Simulated Data

After the API is running:

```bash
python scripts/run_simulator.py --count 100 --satellite-id SAT-001 --anomaly-rate 0.08
```

Stream standalone telemetry JSON once per second:

```bash
python scripts/stream_telemetry.py
```

Example options:

```bash
python scripts/stream_telemetry.py --satellite-id SAT-001 --anomaly-rate 0.08 --count 10
```

Or insert a batch through the API:

```bash
curl -X POST http://localhost:8000/api/v1/telemetry/simulate \
  -H "Content-Type: application/json" \
  -d '{"satellite_id": "SAT-001", "count": 100, "anomaly_rate": 0.08}'
```

## Local Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

The default model trains on recent points for the same satellite. Until the configured training window is reached, scores are stored with `reason="training_pending"`.
Anomaly responses include `anomaly_types`; an Isolation Forest outlier without a specific domain category is labeled `multivariate_outlier`.

The API uses async SQLAlchemy with the `postgresql+asyncpg` driver. If you already created tables with an older schema, recreate the local database volume before running the updated service.

See `docs/architecture.md` for the scalable module layout and extension points.

## Frontend Dashboard

A minimal React + Vite dashboard is included in the `frontend/` folder. It provides live telemetry charts, anomaly alerts, a simple satellite health score, and recent event logs.

Run the dashboard (requires Node.js):

```bash
cd frontend
npm install
npm run dev
```

By default the dashboard points at `http://localhost:8000/api/v1`. You can override the API base with `VITE_API_BASE`.

## Full Project Overview

This repository contains a complete satellite telemetry anomaly detection and monitoring platform. Key components:

- **Backend API** (`app/`): async FastAPI service exposing telemetry ingestion, anomaly queries, metrics, and routes in `app/api/routes`.
- **Anomaly engine** (`app/ai/engines`): `isolation_forest` implementation that combines model scores with domain rules and returns `AnomalyResult` objects with severity and explanations.
- **Standalone engine service**: `app/engine_api.py` exposes a `/score` endpoint for independent scaling of model inference (runs on port 8100 in compose).
- **TelemetryService** (`app/services/telemetry_service.py`): ingests telemetry, trains/scores model, records `AnomalyEvent`s, publishes domain events, and integrates AI reasoning and recommended actions.
- **AI reasoning** (`app/ai/reasoning.py`): deterministic natural-language explanations producing probable cause, severity, and recommended corrective actions.
- **Predictive maintenance** (`app/ai/predictive.py`): windowed RandomForest forecaster that predicts future telemetry and computes a maintenance risk score.
- **Autonomous monitor** (`app/monitor/loop.py` + `scripts/run_monitor.py`): continuous loop reading a telemetry feed, ingesting points, issuing enriched alerts, and storing incidents in daily JSONL reports under `reports/`.
- **Simulator & scripts**: synthetic telemetry generators (`app/simulator`), `scripts/run_simulator.py`, and `scripts/stream_telemetry.py` for testing and demo streams.
- **Frontend dashboard** (`frontend/`): Vite + React app showing live telemetry charts, anomaly alerts, a satellite health score, event logs, and an orbit visualizer.

## Deployment (Docker)

The repository includes a production-ready compose setup with separate services for the API, anomaly engine, frontend, and PostgreSQL. From the repository root:

```bash
docker compose up --build
```

Service mapping (default ports):
- API: http://localhost:8000
- Engine (scoring): http://localhost:8100/score
- Frontend: http://localhost:3000
- Postgres: localhost:5432 (user/password/db: telemetry)

### Notes

- The frontend is built with a `VITE_API_BASE` build-arg so its API target can be overridden at build time. The compose file sets it to `http://api:8000/api/v1` for in-cluster communication.
- The `anomaly-engine` runs the same model logic behind a compact service for horizontal scaling of inference.
- The monitoring pipeline writes daily incident JSONL files to `reports/` (create this directory if you plan to mount it into containers).

## Running locally without Docker

1. Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

2. Frontend

```bash
cd frontend
npm install
npm run dev
```

3. Run simulator or monitor (examples):

```bash
# stream synthetic telemetry to API
python scripts/run_simulator.py --count 100 --satellite-id SAT-001

# run autonomous monitor (simulated feed)
python scripts/run_monitor.py --satellite-id SAT-001
```

## Testing

Unit tests cover anomaly detection, reasoning, predictive forecasting, and service logic.

```bash
pytest
```

## Next steps I can do for you

- Inspect repository files for connectivity and subtle integration issues.
- Start the full Docker Compose stack and watch logs to ensure services start correctly and the frontend communicates with the API. (Confirm when ready — I'll bring the stack up and share logs.)


## Download, Run, Test, and Update (for contributors)

Follow these concise steps to clone the repo, run the system locally, run tests, and contribute updates.

- Clone and enter the repo:

```bash
git clone https://github.com/jdbruh18/Satellite_anomaly-system.git
cd Satellite_anomaly-system
```

- Create a branch for your change:

```bash
git checkout -b feat/your-change
```

- Local Python development (Windows):

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
pytest
```

- Local Python development (macOS / Linux):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest
```

- Run the full stack with Docker Compose (recommended):

```bash
docker compose up --build
```

Service endpoints (after compose):

- API: http://localhost:8000/api/v1
- Engine (scoring): http://localhost:8100/score
- Frontend: http://localhost:3000

- Quick health checks (host):

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health
Invoke-WebRequest http://localhost:8100/health
```

- Regenerate the ONNX surrogate model (if you change the training script or model):

On Windows (PowerShell):
```powershell
cmd /c "set PYTHONPATH=.&& python scripts/export_model_onnx.py"
```

On macOS / Linux:
```bash
PYTHONPATH=. python scripts/export_model_onnx.py
```

- Commit and push updates (recommended workflow):

```bash
# make changes
git add -A
git commit -m "feat: concise summary of change"
git push origin feat/your-change
# open a Pull Request on GitHub and describe the change
```

- Updating the exported model artifact:

1. Regenerate `models/surrogate_score.onnx` using `scripts/export_model_onnx.py`.
2. Run tests: `pytest`.
3. Commit the new model file and any code changes and push the branch.
4. Create a PR and request review; include model provenance and the export command used.

- CI / Tests: add a GitHub Actions workflow to run `pytest` and optionally rebuild the Docker images on PRs. Recommended file: `.github/workflows/ci.yml`.

If you want, I can add a ready-to-use GitHub Actions workflow that runs the tests and lints on each push or PR.


