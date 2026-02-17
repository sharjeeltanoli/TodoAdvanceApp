---
id: 0007
title: Create Cloud Deployment Blueprint Skill
stage: general
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: architect
command: create cloud deployment blueprint skill
labels: ["cloud", "kubernetes", "digitalocean", "cicd", "github-actions", "helm", "skill"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/cloud-deployment-blueprint/SKILL.md
  - .claude/skills/cloud-deployment-blueprint/templates/digitalocean-cluster.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/github-actions-build.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/github-actions-deploy.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/helm-values-production.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/helm-values-staging.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/kubernetes-ingress-prod.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/cert-manager-issuer.yaml.template
  - .claude/skills/cloud-deployment-blueprint/templates/horizontal-pod-autoscaler.yaml.template
  - .claude/skills/cloud-deployment-blueprint/examples/digitalocean-doks-example.yaml
  - .claude/skills/cloud-deployment-blueprint/examples/full-cicd-pipeline-example.yaml
  - .claude/skills/cloud-deployment-blueprint/examples/production-values-example.yaml
tests: []
---

## Prompt

Create a comprehensive Cloud Deployment Blueprint skill for Claude Code.

SKILL PURPOSE:
Generate production-ready cloud deployment configurations and automation scripts for deploying containerized applications to managed Kubernetes services (DigitalOcean DOKS, Azure AKS, Google GKE).

SKILL STRUCTURE:
Create folder: .claude/skills/cloud-deployment-blueprint/

FILES NEEDED:
1. SKILL.md - Main documentation
2. templates/ - 8 template files for cluster config, CI/CD, Helm values, ingress, cert-manager, HPA
3. examples/ - 3 example files for DOKS setup, full pipeline, production values

SKILL.md SHOULD INCLUDE: cloud provider comparison, DOKS setup, GitHub Actions CI/CD, Docker build/push, Helm deployment, SSL/TLS, HPA, production vs staging, rolling deployments, monitoring, cost optimization, rollback strategies.

Make it practical and hackathon-ready for Phase 5C cloud deployment.

## Response

Created the complete Cloud Deployment Blueprint skill with 11 files:

- **SKILL.md**: Comprehensive guide covering cloud provider comparison (DO vs Azure vs GCP recommending DOKS for hackathons), DOKS setup steps, GHCR registry usage, Helm deployment patterns, SSL/TLS with cert-manager, HPA configuration, production vs staging environments, rolling deployments, monitoring (basic + advanced), cost optimization tips, and rollback strategies.

- **8 Templates**: DigitalOcean cluster config, GitHub Actions build (with change detection per service), GitHub Actions deploy (staging auto + production manual + auto-rollback), production Helm values (2+ replicas, HPA, PDB), staging Helm values (1 replica, minimal resources), Kubernetes ingress (TLS, rate limiting, security headers), cert-manager ClusterIssuers (staging + production Let's Encrypt), HPA with scale-up/down policies.

- **3 Examples**: Complete DOKS 8-step setup walkthrough, single-file CI/CD pipeline (test → build → deploy → rollback), real-world production Helm values for hackathon-todo.

All templates use {{VARIABLE}} placeholders and are tailored for the hackathon-todo 3-service architecture (frontend, backend, mcp-server).

## Outcome

SUCCESS - All 11 files created and verified in `.claude/skills/cloud-deployment-blueprint/`.
