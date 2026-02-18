# Research: Event-Driven Todo System

**Feature**: 005-event-driven | **Date**: 2026-02-17 | **Branch**: `005-event-driven`

## R1: Redpanda vs Apache Kafka for Local Development

**Decision**: Use Redpanda as Kafka-compatible broker for both local and production.

**Rationale**:
- Redpanda is a Kafka API-compatible broker written in C++ (no JVM dependency)
- Single binary, ~10x less memory than Kafka+ZooKeeper — ideal for Minikube
- Kafka client libraries (including Dapr's `pubsub.kafka` component) work without modification
- Redpanda Console provides built-in topic/consumer monitoring UI
- Redpanda Cloud offers managed production deployment

**Alternatives Considered**:
- **Apache Kafka**: Requires ZooKeeper (or KRaft mode), 2-3GB+ RAM minimum — too heavy for local Minikube dev
- **Redis Streams (via Dapr `pubsub.redis`)**: Simpler but lacks consumer groups with rebalancing, no replay, no schema registry support
- **NATS JetStream**: Lighter than Kafka but Dapr component is less mature; not Kafka-wire-compatible

**Local Setup**: Redpanda Helm chart (vectorized/redpanda) — single-node, ~256MB RAM, runs on Minikube.

## R2: Dapr Pub/Sub vs Direct Kafka Client

**Decision**: Use Dapr pub/sub abstraction over direct Kafka client libraries.

**Rationale**:
- Constitution Principle IV mandates Dapr as the eventing abstraction layer
- Dapr `pubsub.kafka` component handles connection management, retries, dead-letter queues
- Swapping broker (Redis → Redpanda → managed Kafka) requires only YAML changes, no code changes
- Built-in CloudEvents envelope provides standardized event metadata
- Automatic distributed tracing propagation through sidecar

**Alternatives Considered**:
- **aiokafka / confluent-kafka-python**: Direct Kafka client — more control but couples code to Kafka, violates constitution
- **faststream**: Python async streaming framework — nice DX but bypasses Dapr sidecar mesh

## R3: WebSocket vs Server-Sent Events for Real-Time Client Sync

**Decision**: Use Server-Sent Events (SSE) via a dedicated WebSocket/SSE gateway service.

**Rationale**:
- Frontend already uses SSE for chat streaming (existing pattern)
- SSE is HTTP-based — works through proxies, CDNs, and Kubernetes ingress without special config
- Task updates are server→client only (unidirectional), which is SSE's sweet spot
- The gateway service subscribes to `task-updates` topic via Dapr and fans out to connected clients
- If bidirectional communication is needed later, WebSocket can be added as an upgrade path

**Alternatives Considered**:
- **WebSocket**: Bidirectional but overkill for server-push updates; requires WebSocket-aware ingress/proxy config
- **Long polling**: Simpler but higher latency (violates 2-second SLA) and wastes server resources

## R4: New Microservice Architecture

**Decision**: Add 2 new microservices: Notification Service and WebSocket/SSE Gateway.

**Rationale**:
- **Notification Service**: Subscribes to `reminders` topic, manages notification state (dedup, delivery tracking), exposes API for frontend to fetch notifications. Handles overdue checks via cron binding.
- **WebSocket/SSE Gateway**: Subscribes to `task-updates` topic, maintains SSE connections per user, fans out events to connected clients. Lightweight, stateless (connection state only).
- Recurring task generation stays in the existing backend — it's a subscriber to `task-events` that creates new tasks. Adding a separate service would duplicate DB access patterns.

**Alternatives Considered**:
- **Separate Recurring Task Service**: Would need its own DB connection and task creation logic — over-separation for a single event handler
- **Merging notification + gateway**: Different scaling profiles (notification is bursty, gateway is connection-heavy) — keep separate

## R5: Event Schema and CloudEvents

**Decision**: Use CloudEvents specification (automatic with Dapr pub/sub).

**Rationale**:
- Dapr automatically wraps published messages in CloudEvents envelope
- Provides standardized `id`, `source`, `type`, `specversion`, `time`, `data` fields
- Enables content-based routing in subscriptions (route by `type` field)
- Compatible with event sourcing / audit trail (each event has unique ID and timestamp)

**Event Types**:
- `task.created`, `task.updated`, `task.deleted`, `task.completed` → `task-events` topic
- `reminder.upcoming`, `reminder.overdue` → `reminders` topic
- `sync.task-changed` → `task-updates` topic

## R6: State Store for Caching

**Decision**: Use Redis state store via Dapr for conversation cache and notification dedup.

**Rationale**:
- Redis is already installed by `dapr init` — zero additional infrastructure
- Dapr state store API provides consistent key-value access with TTL support
- Use cases: conversation cache (TTL 1h), reminder dedup (TTL matching reminder window), user preferences
- ETags for optimistic concurrency on shared state

**Alternatives Considered**:
- **PostgreSQL state store**: Possible but adds load to shared Neon DB; Redis is faster for cache patterns
- **In-memory**: Violates Constitution Principle III (stateless services)

## R7: Idempotency Strategy

**Decision**: Use event ID (CloudEvents `id` field) + processed event log table for consumer idempotency.

**Rationale**:
- Each Dapr event has a unique `id` in the CloudEvents envelope
- Consumers check `processed_events` table before processing; insert on success (within same transaction)
- TTL-based cleanup of processed_events (7 days, matching broker retention)
- For notification dedup: use Dapr state store with `reminder:{task_id}:{window}` key and TTL

## R8: Observability for Event-Driven System

**Decision**: Extend existing observability stack with Dapr-specific metrics and traces.

**Rationale**:
- Dapr sidecars emit Prometheus metrics automatically (pub/sub delivery count, latency, errors)
- Dapr tracing config forwards spans to Jaeger (already in monitoring namespace from Phase 3)
- Add custom metrics: events_published_total, events_consumed_total, consumer_lag_seconds
- Alert on: consumer lag > 10s, dead-letter topic messages > 0, pub/sub errors > threshold
