# Architecture

This project is organized around a scalable async FastAPI service with clear boundaries between HTTP routes, application services, persistence, AI engines, integrations, and operational concerns.

```text
app/
  ai/
    base.py                    AI model protocols
    engines/                   anomaly model implementations
  api/
    dependencies.py            dependency injection and service assembly
    routes/                    HTTP route modules
  core/                        settings and logging
  db/                          async SQLAlchemy engine, sessions, repositories
  events/                      event publisher interfaces
  integrations/                external telemetry feed clients
  models/                      database models
  observability/               metrics and runtime telemetry
  schemas/                     Pydantic API contracts
  services/                    application use cases
  simulator/                   synthetic telemetry generation
  workers/                     background and batch jobs
```

## Flow

1. API routes receive validated telemetry JSON requests.
2. `app.api.dependencies` assembles repositories, AI engines, and services.
3. `TelemetryService` trains the anomaly engine on recent normal telemetry for the same satellite, stores the telemetry point with timestamps, scores it, records the anomaly event, emits domain events, logs activity, and updates metrics.
4. Async repositories isolate PostgreSQL queries from business logic.
5. AI engines live behind a protocol so additional models can be added without changing route handlers.

## Scaling Paths

- Replace `LoggingEventPublisher` with Kafka, RabbitMQ, Redis Streams, or another event bus.
- Move `app.workers.jobs` into Celery, RQ, Dramatiq, or a Kubernetes CronJob.
- Add model versions under `app/ai/engines` and route selection through configuration.
- Export `app.observability.metrics` to Prometheus or OpenTelemetry.
- Add external satellite providers under `app/integrations`.

## Anomaly Detection

`app.ai.engines.isolation_forest.AnomalyEngine` fits an Isolation Forest on telemetry previously classified as normal. It combines the model score with domain-aware classification for:

- `temperature_spike`: CPU temperature exceeds the learned normal range.
- `power_drop`: battery voltage or solar output falls below normal operating range.
- `signal_instability`: signal strength drops sharply against the learned baseline.
- `fuel_anomaly`: fuel level is unusually low or drops suddenly.
- `multivariate_outlier`: Isolation Forest detects an outlier without a single domain category.

## Extended Components

- **AI Reasoning:** `app/ai/reasoning.py` produces deterministic natural-language explanations for anomaly events including probable cause, severity, and recommended corrective actions. This is used by `TelemetryService` to enrich persisted `AnomalyEvent`s and alerts.

- **Predictive Maintenance:** `app/ai/predictive.py` trains a windowed RandomForest regressor on recent telemetry and forecasts future telemetry values; a maintenance risk heuristic flags satellites needing attention.

- **Autonomous Monitor:** `app/monitor/loop.py` reads telemetry from a `TelemetryFeedClient` (simulator or external integration), ingests points via `TelemetryService`, forwards enriched alerts via `AlertManager`, and appends incidents to daily JSONL report files.

- **Frontend Dashboard:** built with Vite + React and served as static files from Nginx in production. The dashboard polls the API for telemetry and anomaly events and displays live charts, alerts, a health score, event logs, and an orbit visualizer.

## Data Flow (detailed)

1. Telemetry ingestion starts at API route `POST /api/v1/telemetry` or via the monitor/simulator feeds.
2. `TelemetryService.ingest` retrieves recent normal history from `TelemetryRepository`, trains or updates the `AnomalyEngine` as needed, scores the incoming point, and invokes the AI reasoning module to produce an explanation and recommended action.
3. The result is persisted in `AnomalyEvent`, metrics are incremented, and a domain event is published using `EventPublisher` (default: `LoggingEventPublisher`).
4. The `AutonomousMonitor` and `AlertManager` forward enriched alerts to configured sinks (webhook, logs). Incident reports are appended to `reports/` for operational review.
5. The frontend polls the API to visualize telemetry, anomalies, and maintenance recommendations.

## Scaling & Production Considerations

- Split inference (anomaly engine) into its own service for horizontal scaling and autoscaling under load. Keep model versions immutable and loadable from a model store.
- Persist model training metadata and roll up statistics for drift detection and retraining triggers.
- Add secure authentication + RBAC for dashboard and API endpoints.
- Use robust observability: export metrics to Prometheus and traces to a tracing backend (Jaeger / OpenTelemetry).

