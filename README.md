# Automobile Company Microservices Platform

A modern connected-car platform built with 12 independent microservices, designed for scalability, maintainability, and cloud-native deployment.

## Architecture Overview

This platform consists of 12 microservices:

1. **auth-api** - Authentication & JWT authorization
2. **users-api** - User profiles management
3. **vehicles-api** - Vehicle data management
4. **orders-api** - Car order management
5. **inventory-api** - Stock and spare parts management
6. **payments-api** - Transaction processing
7. **telemetry-api** - IoT vehicle telemetry
8. **geofence-api** - Geofencing and location services
9. **notifications-api** - Email/SMS/Push notifications
10. **billing-api** - Subscription & billing management
11. **dealer-portal** - Dealer-facing web frontend
12. **reports-api** - Analytics and reporting

## Tech Stack

- **Backend**: Python (FastAPI)
- **Container**: Docker
- **Orchestration**: Kubernetes (Helm charts)
- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform
- **Developer Portal**: Backstage.io
- **Testing**: pytest

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Kubernetes (kind/minikube for local, EKS for production)
- Helm 3+
- Terraform
- Python 3.11+

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd automobile-platform

# Start all services with Docker Compose
docker-compose up -d

# Or deploy to local Kubernetes
./scripts/deploy-local.sh
```

### Production Deployment

```bash
# Apply Terraform infrastructure
cd terraform/
terraform init
terraform apply

# Deploy services with Helm
./scripts/deploy-production.sh
```

## Service Architecture

Each microservice follows the same structure:
```
service-name/
├── src/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   └── services/
├── tests/
├── charts/
├── Dockerfile
├── pyproject.toml
└── README.md
```

## API Documentation

Each service exposes OpenAPI documentation at `/docs` endpoint.

## Monitoring & Observability

- Health checks at `/healthz`
- Metrics at `/metrics`
- Distributed tracing with OpenTelemetry
- Centralized logging

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License
