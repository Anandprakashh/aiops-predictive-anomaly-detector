# AIOps Predictive Anomaly Detector

This project is **Phase 2** of my `dev-platform-aiops-lab` GitOps/DevOps platform.  
It adds an AIOps/ML layer that detects anomalous error bursts in application logs stored in Elasticsearch and exposes a simple `/predict` API that can drive automated rollback or other GitOps actions.

## What it Does

- Reads recent log events from an Elasticsearch index (e.g. `chaos-logs`).
- Engineers simple features from log records (error level, message patterns, length).
- Trains an Isolation Forest model to score anomalies on the fly.
- Exposes a Flask endpoint `/predict` that:
  - Queries Elasticsearch for the last *N* minutes of logs.
  - Runs the Isolation Forest model.
  - Returns a JSON signal: `anomaly: true/false` plus a list of top anomalous log entries.
- Runs as a Kubernetes Deployment in its own `aiops` namespace.
- Uses a Kubernetes CronJob to call `/predict` on a schedule for continuous anomaly checks.
- Visualizes error/anomaly logs in Grafana using the `chaos-logs` index.

## Tech Stack

- Kubernetes, Argo CD (GitOps), CronJob
- Python, Flask, scikit-learn (Isolation Forest)
- Elasticsearch (log storage)
- Grafana (log/anomaly visualization)

## Components

- `app/` – Flask API and ML logic (`/health`, `/predict`, Isolation Forest model).
- `k8s/` – Kubernetes manifests:
  - `deployment.yaml` and `service.yaml` for the `aiops-detector` service in the `aiops` namespace.
  - `cronjob.yaml` that calls `/predict` every few minutes.
  - `chaos-app.yaml` test workload that generates controlled error logs.
- `dashboards/grafana-dashboard.json` – Exported Grafana dashboard showing chaos/anomaly logs from Elasticsearch.
- `infra/` – Notes/placeholders for the logging and monitoring stack (Elasticsearch, Kibana, Prometheus, Grafana) deployed via Helm in separate namespaces.

## Relationship to dev-platform-aiops-lab

This repository extends the existing `dev-platform-aiops-lab` project with a dedicated AIOps / ML anomaly detection module.  
The base cluster, logging stack (Elasticsearch + Kibana) and monitoring stack (Prometheus + Grafana) are provisioned in `dev-platform-aiops-lab`; this module is deployed on top into the `aiops` namespace and consumes logs from Elasticsearch to provide an anomaly signal that can be wired into GitOps (Argo CD / Argo Rollouts) for automated rollback in future iterations.
