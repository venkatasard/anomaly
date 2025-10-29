# Anomaly

Anomaly is a full-stack operations intelligence platform. It accepts metrics and logs through Kafka, detects statistical deviations, indexes log meaning with pgvector, correlates incidents, and produces evidence-based investigations using Gemini.

## Architecture

`clients → FastAPI → Kafka → pipeline worker → PostgreSQL/pgvector → Gemini`

Redis provides cross-replica realtime fan-out to WebSocket clients. The web application uses Next.js, TypeScript, Tailwind CSS, Zustand, and Recharts.

## Run locally

1. Copy `.env.example` to `.env`. A Gemini key is optional; without it, deterministic local embeddings and clearly conservative investigation text keep the development workflow functional.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`; API documentation is at `http://localhost:8000/docs`.
4. Seed services with `make seed` and produce 60,000 mixed healthy/failure events with `make simulate`.

The simulator emits five services, periodic latency and resource spikes, traffic drops, log spikes, and database timeout bursts. With its default cadence it also generates more than 3,000 searchable log embeddings.

## APIs and realtime

The API implements event/log ingestion, anomaly filtering, incident creation and state updates, service health, operational analytics, stream metrics, semantic search, and incident detail. WebSocket endpoints are `/ws/events`, `/ws/anomalies`, `/ws/incidents`, and `/ws/service-health`.

## Production notes

- Replace all example secrets, terminate TLS at the edge, and restrict CORS.
- Use managed PostgreSQL with the vector extension, a replicated Kafka cluster, and authenticated Redis.
- Run multiple API and worker replicas; Redis pub/sub synchronizes connected clients.
- Configure Kafka retention, dead-letter handling, schema validation, rate limits, and observability appropriate to your environment.
- The included authentication screen is a UI boundary. Integrate your identity provider before exposing the deployment.

## Tests

Run `cd backend && pip install -e '.[dev]' && pytest`. Build-check the UI with `cd frontend && npm install && npm run build`.

## Data ownership

Runtime persistence uses SQLAlchemy and Alembic. The complete requested Prisma representation is provided in `prisma/schema.prisma` for tooling and schema review; it maps to the same PostgreSQL tables.
