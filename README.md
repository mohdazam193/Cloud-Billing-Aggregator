# ☁️ Cloud Billing Aggregator

![CI](https://github.com/your-username/cloud-billing-aggregator/actions/workflows/ci-cd.yml/badge.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Deployed-blueviolet)
![Status](https://img.shields.io/badge/Status-Capstone%20Ready-success)

A **Kubernetes-native, multi-cloud billing aggregation and visualization platform**
that fetches **real AWS and Azure cost data**, built as an **SRE / DevOps Capstone Project**.

---

## 📌 Overview

Organizations running workloads across multiple cloud providers lack a **single pane of glass**
for cost visibility. **Cloud Billing Aggregator** provides:

- Secure login-based access
- Cloud credential onboarding
- Real AWS & Azure billing data
- Cost visualizations and service-level insights
- Kubernetes-native deployment with CI/CD

---

## ✨ Key Features

- 🔐 Demo login (session-based authentication)
- ☁️ Multi-cloud billing (AWS + Azure)
- 📊 Cost visualization
  - Total cost summary
  - AWS vs Azure split
  - Service-level cost breakdown
- 🧠 Session-only credential handling
- 🎨 Modern UI (React + Tailwind)
- ⚙️ FastAPI backend
- ☸️ Kubernetes deployment
- 🔄 GitHub Actions CI/CD

---

## 🧱 Architecture

### High-Level Architecture Diagram

Add image at:
```
docs/architecture-diagram.png
```

```md
![Architecture Diagram](docs/architecture-diagram.png)
```

### Logical Architecture (Text)

```
Browser (React)
   |
Frontend (Nginx)
   |
Backend (FastAPI)
   |
AWS Cost Explorer + Azure Cost Management
```

---

## 🖼️ Screenshots

Add screenshots under `/screenshots`

```md
![Login](screenshots/login.png)
![Credentials](screenshots/cloud-credentials.png)
![Dashboard](screenshots/dashboard.png)
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|-----|-----------|
| Frontend | React, Tailwind, Recharts |
| Backend | FastAPI |
| Cloud APIs | AWS CE, Azure CM |
| Containers | Docker |
| Orchestration | Kubernetes |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
cloud-billing-aggregator/
├── backend/
├── frontend/
├── k8s/
├── .github/workflows/
├── docs/
└── screenshots/
```

---

## 🚀 Getting Started

### Prerequisites
- Docker
- Kubernetes (Minikube / Docker Desktop / Kind)
- kubectl
- AWS & Azure billing access

---

### Clone Repository
```bash
git clone https://github.com/your-username/cloud-billing-aggregator.git
cd cloud-billing-aggregator
```

---

### Build Images
```bash
docker build -t billing-backend backend/
docker build -t billing-frontend frontend/
```

---

### Deploy to Kubernetes
```bash
kubectl apply -f k8s/
```

---

### Access Application
```bash
kubectl port-forward deployment/billing-frontend 8080:80
```

Open:
```
http://localhost:8080
```

---

## 🔑 Demo Credentials

```
Username: Napster193
Password: ChangeMe123
```

---

## ☁️ Cloud Permissions

### AWS
- Permission: `ce:GetCostAndUsage`

### Azure
- Role: Cost Management Reader
- Subscription ID required

---

## 🔄 CI/CD Pipeline

- GitHub Actions
- Triggered on push to `main`
- Builds frontend and backend images

---

## 🎓 Capstone Justification

This project demonstrates:
- Multi-cloud cost observability
- Kubernetes-native deployment
- CI/CD pipelines
- Secure session handling
- SRE / DevOps best practices

---

## ⚠️ Disclaimer

Educational / capstone project only.
Not production-hardened.

---

## 📜 License
MIT License

---

## 🙌 Author
SRE / DevOps Capstone Project
