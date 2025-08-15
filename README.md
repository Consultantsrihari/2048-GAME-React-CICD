# Automobile Company Microservices Platform

A modern connected-car platform built with 12 independent microservices, designed for scalability, maintainability, and developer productivity.

## 🚗 Architecture Overview

This platform consists of 12 microservices that work together to provide a comprehensive automobile management system:

### Core Services
- **orders-api** - Manage car orders and order lifecycle
- **inventory-api** - Manage stock and spare parts inventory
- **payments-api** - Handle payment transactions and processing
- **auth-api** - Authentication & JWT authorization
- **users-api** - User profile management
- **vehicles-api** - Vehicle data and specifications

### Connected Car Services
- **telemetry-api** - IoT vehicle telemetry data collection
- **geofence-api** - Geofencing and location services
- **notifications-api** - Email/SMS/Push notifications
- **billing-api** - Subscription & billing management
- **dealer-portal** - Dealer-facing web frontend
- **reports-api** - Analytics and reporting

## 🏗️ Project Structure

```
automobile-company/
├── services/                    # Microservices
│   ├── orders-api/
│   ├── inventory-api/
│   ├── payments-api/
│   ├── auth-api/
│   ├── users-api/
│   ├── vehicles-api/
│   ├── telemetry-api/
│   ├── geofence-api/
│   ├── notifications-api/
│   ├── billing-api/
│   ├── dealer-portal/
│   └── reports-api/
├── infrastructure/              # Infrastructure as Code
│   ├── terraform/
│   ├── kubernetes/
│   └── helm/
├── ci-cd/                      # CI/CD Pipelines
│   └── github-actions/
├── backstage/                  # Developer Portal
│   ├── catalog/
│   └── templates/
├── docs/                       # Documentation
└── scripts/                    # Utility Scripts
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Kubernetes cluster (kind, minikube, or EKS)
- Helm 3.x
- Terraform 1.x
- Python 3.9+

### Local Development

1. **Start Local Kubernetes Cluster**
   ```bash
   # Using kind
   kind create cluster --name automobile-cluster
   
   # Or using minikube
   minikube start
   ```

2. **Deploy Infrastructure**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform apply
   ```

3. **Deploy Services**
   ```bash
   # Deploy all services
   ./scripts/deploy-all.sh
   
   # Or deploy individual service
   helm install orders-api charts/orders-api/ -n orders-api-dev
   ```

4. **Access Services**
   ```bash
   # Port forward to access services
   kubectl port-forward svc/orders-api 8000:8000 -n orders-api-dev
   
   # Access health endpoint
   curl http://localhost:8000/healthz
   ```

## 🧪 Testing

### Run All Tests
```bash
./scripts/test-all.sh
```

### Run Individual Service Tests
```bash
cd services/orders-api
pytest tests/
```

## 📊 Monitoring & Observability

- **Health Checks**: Each service exposes `/healthz` endpoint
- **Metrics**: Prometheus metrics at `/metrics`
- **Logging**: Structured JSON logging
- **Tracing**: Distributed tracing with OpenTelemetry

## 🔐 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Service-to-service authentication
- Secrets management with Kubernetes secrets
- Network policies for service isolation

## 📚 Documentation

Each service includes:
- API documentation (OpenAPI/Swagger)
- Service-specific README
- Architecture diagrams
- Deployment guides

## 🤝 Contributing

1. Use the Backstage developer portal to create new services
2. Follow the established patterns and templates
3. Ensure all tests pass before submitting PRs
4. Update documentation for any changes

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Check service-specific README files
- Review API documentation
- Open issues in the repository
- Contact the platform team

---

**Built with ❤️ for the modern connected-car ecosystem**
