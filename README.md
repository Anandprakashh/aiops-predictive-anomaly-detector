# AIOps Predictive Anomaly Detector

This project is **Phase 2** of my `dev-platform-aiops-lab` GitOps/DevOps platform.  
It adds an AIOps/ML layer that predicts anomalies from application logs and triggers automated rollback via GitOps.

## What it Does

- Collects logs from Kubernetes workloads (via Elasticsearch / Fluent Bit).
- Trains an ML model (Isolation Forest) to detect abnormal error patterns.
- Exposes a Flask endpoint to score recent logs.
- Runs a Kubernetes CronJob that:
  - Queries logs,
  - Calls the ML model,
  - Triggers Argo Rollouts rollback when anomaly score is high.
- Visualizes anomaly scores and events in Grafana.

## Tech Stack

- Kubernetes, Argo CD, Argo Rollouts
- Python, Flask, scikit-learn
- Elasticsearch, Fluent Bit
- Grafana, Prometheus

## Relationship to dev-platform-aiops-lab

This repository extends the existing `dev-platform-aiops-lab` project with a dedicated AIOps / ML anomaly detection module.  
Use that project to provision the base cluster and GitOps plumbing, then deploy this module on top.

