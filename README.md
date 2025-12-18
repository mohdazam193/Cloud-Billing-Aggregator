# Cloud Billing Aggregator

CloudZero-inspired multi-cloud cost aggregation tool.

## Stack
- FastAPI
- HTML + CSS (modern SaaS UI)
- Chart.js
- AWS Cost Explorer
- Azure Cost Management
- Docker
- Kubernetes

## Run locally
```bash
docker build -t cloud-billing-aggregator:latest backend/
kubectl apply -f k8s/
kubectl port-forward svc/cloud-billing-aggregator 8080:8000
