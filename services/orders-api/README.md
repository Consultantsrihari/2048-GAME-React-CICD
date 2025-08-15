# Orders API

Orders management microservice for the Automobile Company platform. This service handles the complete order lifecycle from creation to fulfillment.

## 🚗 Overview

The Orders API is responsible for:
- Creating and managing car orders
- Tracking order status and payment status
- Managing order items and accessories
- Integrating with payment and inventory services
- Providing order analytics and reporting

## 🏗️ Architecture

### Components
- **FastAPI Application**: RESTful API with OpenAPI documentation
- **SQLAlchemy ORM**: Database abstraction and migrations
- **PostgreSQL**: Primary data store for orders
- **Redis**: Caching and session management
- **Prometheus**: Metrics collection
- **OpenTelemetry**: Distributed tracing

### External Dependencies
- **Auth API**: User authentication and authorization
- **Payments API**: Payment processing and status updates
- **Inventory API**: Vehicle and parts availability
- **Notifications API**: Order status notifications

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose

### Local Development

1. **Clone and setup**
   ```bash
   cd services/orders-api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

3. **Database Setup**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d postgresql redis
   
   # Run migrations
   alembic upgrade head
   ```

4. **Run the Application**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/healthz
   - Metrics: http://localhost:8000/metrics

### Docker Development

```bash
# Build the image
docker build -t orders-api:latest .

# Run with Docker Compose
docker-compose up -d
```

## 📚 API Documentation

### Endpoints

#### Health & Monitoring
- `GET /healthz` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /` - Root endpoint

#### Orders Management
- `POST /api/v1/orders` - Create new order
- `GET /api/v1/orders` - List orders (with filtering)
- `GET /api/v1/orders/{order_id}` - Get order by ID
- `GET /api/v1/orders/number/{order_number}` - Get order by number
- `PUT /api/v1/orders/{order_id}` - Update order
- `DELETE /api/v1/orders/{order_id}` - Delete order

#### Order Status Management
- `PATCH /api/v1/orders/{order_id}/status` - Update order status
- `PATCH /api/v1/orders/{order_id}/payment` - Update payment status

### Request/Response Examples

#### Create Order
```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-123",
    "vehicle_id": "vehicle-456",
    "quantity": 1,
    "unit_price": "25000.00",
    "currency": "USD",
    "shipping_address": "123 Main St, City, State 12345",
    "billing_address": "123 Main St, City, State 12345",
    "payment_method": "credit_card",
    "notes": "Test order",
    "dealer_id": "dealer-789",
    "order_items": [
      {
        "item_id": "accessory-1",
        "item_name": "Premium Sound System",
        "item_type": "accessory",
        "quantity": 1,
        "unit_price": "1500.00"
      }
    ]
  }'
```

#### Get Orders with Filtering
```bash
curl "http://localhost:8000/api/v1/orders?customer_id=customer-123&status=pending&page=1&size=10"
```

#### Update Order Status
```bash
curl -X PATCH "http://localhost:8000/api/v1/orders/1/status" \
  -H "Content-Type: application/json" \
  -d '{
    "order_status": "confirmed",
    "notes": "Order confirmed by dealer"
  }'
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_orders.py

# Run with verbose output
pytest -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Database and external service integration
- **API Tests**: Endpoint testing with FastAPI TestClient

## 🐳 Docker

### Build Image
```bash
# Development build
docker build --target development -t orders-api:dev .

# Production build
docker build --target production -t orders-api:prod .
```

### Docker Compose
```yaml
version: '3.8'
services:
  orders-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgresql:5432/orders_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgresql
      - redis
```

## ☸️ Kubernetes Deployment

### Helm Chart
```bash
# Install the chart
helm install orders-api charts/orders-api/ -n orders-api-dev

# Upgrade existing deployment
helm upgrade orders-api charts/orders-api/ -n orders-api-dev

# Uninstall
helm uninstall orders-api -n orders-api-dev
```

### Configuration
The Helm chart supports various configuration options:
- Replica count and scaling
- Resource limits and requests
- Environment variables and secrets
- Ingress configuration
- Monitoring and logging

## 📊 Monitoring & Observability

### Metrics
- HTTP request count and duration
- Database connection pool status
- Order creation and processing rates
- Error rates and response times

### Logging
- Structured JSON logging
- Request/response correlation
- Error tracking and debugging
- Performance monitoring

### Tracing
- Distributed tracing with OpenTelemetry
- Service-to-service call tracking
- Performance bottleneck identification

## 🔐 Security

### Authentication
- JWT-based authentication
- Role-based access control (RBAC)
- Service-to-service authentication

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting

### Secrets Management
- Kubernetes secrets for sensitive data
- Environment variable encryption
- Secure configuration management

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `STRIPE_SECRET_KEY` | Stripe API key | - |
| `LOG_LEVEL` | Logging level | `INFO` |

### Database Schema
The service uses the following main tables:
- `orders`: Main order information
- `order_items`: Order line items and accessories

## 🤝 Contributing

1. Follow the established code patterns
2. Write tests for new features
3. Update documentation
4. Ensure all tests pass
5. Follow the commit message conventions

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- Check the API documentation
- Review the logs and metrics
- Open an issue in the repository
- Contact the platform team

---

**Part of the Automobile Company Microservices Platform**