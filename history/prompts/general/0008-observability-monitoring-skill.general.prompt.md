---
id: 0008
title: Create Observability and Monitoring Skill
stage: general
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: architect
command: create observability and monitoring skill
labels: ["observability", "monitoring", "prometheus", "grafana", "loki", "jaeger", "logging", "alerting", "skill"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/observability-monitoring/SKILL.md
  - .claude/skills/observability-monitoring/templates/prometheus-servicemonitor.yaml.template
  - .claude/skills/observability-monitoring/templates/grafana-dashboard.json.template
  - .claude/skills/observability-monitoring/templates/loki-config.yaml.template
  - .claude/skills/observability-monitoring/templates/jaeger-deployment.yaml.template
  - .claude/skills/observability-monitoring/templates/alertmanager-rules.yaml.template
  - .claude/skills/observability-monitoring/templates/structured-logging-python.template
  - .claude/skills/observability-monitoring/templates/structured-logging-nextjs.template
  - .claude/skills/observability-monitoring/examples/todo-app-prometheus-example.yaml
  - .claude/skills/observability-monitoring/examples/todo-app-grafana-dashboard-example.json
  - .claude/skills/observability-monitoring/examples/python-structured-logging-example.py
  - .claude/skills/observability-monitoring/examples/nextjs-logging-example.ts
tests: []
---

## Prompt

Create a comprehensive Observability and Monitoring skill for Claude Code. Generate production-ready observability configurations including logging, metrics, tracing, and alerting for containerized applications on Kubernetes. Covers three pillars: Logs (Loki + structlog/pino), Metrics (Prometheus + Grafana), Traces (Jaeger + OpenTelemetry). Templates for ServiceMonitors, Grafana dashboards, Loki config, Jaeger deployment, AlertManager rules, and structured logging for Python/FastAPI and Next.js. Best practices include RED/USE metrics, correlation IDs, JSON structured logging, and cost-effective in-cluster setup.

## Response

Created the complete Observability and Monitoring skill with 12 files:

- **SKILL.md**: Comprehensive guide covering the three observability pillars (logs, metrics, traces), full stack overview (Prometheus, Grafana, Loki, Jaeger, AlertManager), quick-start install commands, Prometheus metrics collection with FastAPI integration, Grafana dashboard patterns, Loki log aggregation with LogQL examples, Jaeger distributed tracing setup, alert rules with severity levels, Python/FastAPI structured logging with structlog, Next.js logging with pino, K8s health monitoring, Dapr observability integration, cost-effective tiered setup ($0 in-cluster), and retention policies.

- **7 Templates**: Prometheus ServiceMonitor with recording rules, Grafana dashboard JSON with RED metrics/resources/logs panels, Loki config with Promtail pipeline stages, Jaeger all-in-one deployment with OTLP support, AlertManager rules (availability/performance/errors/resources/database/application), Python structured logging with structlog + middleware + Prometheus metrics, Next.js structured logging with pino + client-side error reporting.

- **4 Examples**: Complete Prometheus setup for hackathon-todo with ServiceMonitors/recording rules/alerts, ready-to-import Grafana dashboard with overview stats + RED metrics + resource panels, runnable Python/FastAPI structured logging implementation, working Next.js/pino logging with server + client patterns.

## Outcome

SUCCESS - All 12 files created and verified in `.claude/skills/observability-monitoring/`.
