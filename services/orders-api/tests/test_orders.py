"""
Tests for Orders API.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.order import Order, OrderStatus, PaymentStatus
from src.schemas.order import OrderCreate, OrderItemCreate

client = TestClient(app)


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
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
    }


@pytest.fixture
def sample_order():
    """Sample order object for testing."""
    return Order(
        id=1,
        order_number="ORD-20231201-ABC12345",
        customer_id="customer-123",
        vehicle_id="vehicle-456",
        quantity=1,
        unit_price=Decimal("25000.00"),
        total_amount=Decimal("26500.00"),
        currency="USD",
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        shipping_address="123 Main St, City, State 12345",
        billing_address="123 Main St, City, State 12345",
        payment_method="credit_card",
        notes="Test order",
        dealer_id="dealer-789"
    )


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "orders-api"
        assert data["version"] == "0.1.0"


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Orders API - Automobile Company"


class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    def test_metrics(self):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestOrdersAPI:
    """Test orders API endpoints."""
    
    @patch('src.api.v1.orders.OrderService')
    def test_create_order(self, mock_service, sample_order_data, sample_order):
        """Test creating a new order."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.create_order.return_value = sample_order
        mock_service.return_value = mock_service_instance
        
        response = client.post("/api/v1/orders", json=sample_order_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["order_number"] == sample_order.order_number
        assert data["customer_id"] == sample_order.customer_id
        assert data["vehicle_id"] == sample_order.vehicle_id
        assert data["total_amount"] == str(sample_order.total_amount)
    
    @patch('src.api.v1.orders.OrderService')
    def test_get_orders(self, mock_service, sample_order):
        """Test getting orders list."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.get_orders.return_value = ([sample_order], 1)
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/orders")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["size"] == 20
        assert len(data["orders"]) == 1
        assert data["orders"][0]["order_number"] == sample_order.order_number
    
    @patch('src.api.v1.orders.OrderService')
    def test_get_order_by_id(self, mock_service, sample_order):
        """Test getting order by ID."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.get_order.return_value = sample_order
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/orders/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_order.id
        assert data["order_number"] == sample_order.order_number
    
    @patch('src.api.v1.orders.OrderService')
    def test_get_order_by_id_not_found(self, mock_service):
        """Test getting order by ID when not found."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.get_order.return_value = None
        mock_service.return_value = mock_service_instance
        
        response = client.get("/api/v1/orders/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"
    
    @patch('src.api.v1.orders.OrderService')
    def test_get_order_by_number(self, mock_service, sample_order):
        """Test getting order by order number."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.get_order_by_number.return_value = sample_order
        mock_service.return_value = mock_service_instance
        
        response = client.get(f"/api/v1/orders/number/{sample_order.order_number}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["order_number"] == sample_order.order_number
    
    @patch('src.api.v1.orders.OrderService')
    def test_update_order(self, mock_service, sample_order):
        """Test updating order."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.update_order.return_value = sample_order
        mock_service.return_value = mock_service_instance
        
        update_data = {
            "notes": "Updated test order"
        }
        
        response = client.put("/api/v1/orders/1", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["notes"] == sample_order.notes
    
    @patch('src.api.v1.orders.OrderService')
    def test_update_order_status(self, mock_service, sample_order):
        """Test updating order status."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.update_order_status.return_value = sample_order
        mock_service.return_value = mock_service_instance
        
        status_data = {
            "order_status": "confirmed",
            "notes": "Order confirmed"
        }
        
        response = client.patch("/api/v1/orders/1/status", json=status_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["order_status"] == sample_order.order_status.value
    
    @patch('src.api.v1.orders.OrderService')
    def test_update_payment_status(self, mock_service, sample_order):
        """Test updating payment status."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.update_payment_status.return_value = sample_order
        mock_service.return_value = mock_service_instance
        
        payment_data = {
            "payment_status": "paid",
            "payment_intent_id": "pi_1234567890",
            "notes": "Payment completed"
        }
        
        response = client.patch("/api/v1/orders/1/payment", json=payment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["payment_status"] == sample_order.payment_status.value
    
    @patch('src.api.v1.orders.OrderService')
    def test_delete_order(self, mock_service):
        """Test deleting order."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.delete_order.return_value = True
        mock_service.return_value = mock_service_instance
        
        response = client.delete("/api/v1/orders/1")
        assert response.status_code == 204
    
    @patch('src.api.v1.orders.OrderService')
    def test_delete_order_not_found(self, mock_service):
        """Test deleting order when not found."""
        # Mock the service
        mock_service_instance = AsyncMock()
        mock_service_instance.delete_order.return_value = False
        mock_service.return_value = mock_service_instance
        
        response = client.delete("/api/v1/orders/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"


class TestOrderValidation:
    """Test order validation."""
    
    def test_create_order_invalid_currency(self):
        """Test creating order with invalid currency."""
        invalid_data = {
            "customer_id": "customer-123",
            "vehicle_id": "vehicle-456",
            "quantity": 1,
            "unit_price": "25000.00",
            "currency": "INVALID",  # Invalid 3-letter code
            "order_items": []
        }
        
        response = client.post("/api/v1/orders", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_order_negative_price(self):
        """Test creating order with negative price."""
        invalid_data = {
            "customer_id": "customer-123",
            "vehicle_id": "vehicle-456",
            "quantity": 1,
            "unit_price": "-100.00",  # Negative price
            "currency": "USD",
            "order_items": []
        }
        
        response = client.post("/api/v1/orders", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_order_zero_quantity(self):
        """Test creating order with zero quantity."""
        invalid_data = {
            "customer_id": "customer-123",
            "vehicle_id": "vehicle-456",
            "quantity": 0,  # Zero quantity
            "unit_price": "25000.00",
            "currency": "USD",
            "order_items": []
        }
        
        response = client.post("/api/v1/orders", json=invalid_data)
        assert response.status_code == 422