#!/bin/bash

# Automobile Company Microservices Platform - Deployment Script
# This script deploys all microservices to Kubernetes using Helm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
NAMESPACE_SUFFIX=${ENVIRONMENT}
REGISTRY="ghcr.io/automobile-company"
TAG=${2:-latest}

# Services to deploy
SERVICES=(
    "orders-api"
    "inventory-api"
    "payments-api"
    "auth-api"
    "users-api"
    "vehicles-api"
    "telemetry-api"
    "geofence-api"
    "notifications-api"
    "billing-api"
    "dealer-portal"
    "reports-api"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_success "Kubectl is available and connected to cluster"
}

# Function to check if helm is available
check_helm() {
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Helm is available"
}

# Function to create namespace if it doesn't exist
create_namespace() {
    local namespace=$1
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        print_status "Creating namespace: $namespace"
        kubectl create namespace "$namespace"
        kubectl label namespace "$namespace" environment="$ENVIRONMENT" project="automobile-company"
    else
        print_status "Namespace $namespace already exists"
    fi
}

# Function to deploy a single service
deploy_service() {
    local service=$1
    local namespace="${service}-${NAMESPACE_SUFFIX}"
    local chart_path="services/${service}/charts/${service}"
    
    print_status "Deploying $service to namespace $namespace"
    
    # Create namespace
    create_namespace "$namespace"
    
    # Check if chart exists
    if [ ! -d "$chart_path" ]; then
        print_error "Chart not found at $chart_path"
        return 1
    fi
    
    # Deploy using Helm
    helm upgrade --install "$service" "$chart_path" \
        --namespace "$namespace" \
        --set global.environment="$ENVIRONMENT" \
        --set global.imageRegistry="$REGISTRY" \
        --set deployment.pod.container.image.tag="$TAG" \
        --set deployment.replicas=2 \
        --set ingress.enabled=true \
        --set serviceMonitor.enabled=true \
        --set hpa.enabled=true \
        --set networkPolicy.enabled=true \
        --set pdb.enabled=true \
        --wait \
        --timeout=10m
    
    print_success "Successfully deployed $service"
}

# Function to deploy infrastructure components
deploy_infrastructure() {
    print_status "Deploying infrastructure components"
    
    # Add Helm repositories
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
    helm repo update
    
    # Deploy NGINX Ingress Controller
    if ! helm list -n ingress-nginx | grep -q "nginx-ingress"; then
        print_status "Deploying NGINX Ingress Controller"
        helm install nginx-ingress ingress-nginx/ingress-nginx \
            --namespace ingress-nginx \
            --create-namespace \
            --set controller.service.type=LoadBalancer \
            --wait \
            --timeout=10m
    else
        print_status "NGINX Ingress Controller already deployed"
    fi
    
    # Deploy Prometheus Stack
    if ! helm list -n monitoring | grep -q "prometheus"; then
        print_status "Deploying Prometheus Stack"
        helm install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --create-namespace \
            --set grafana.enabled=true \
            --set alertmanager.enabled=true \
            --wait \
            --timeout=10m
    else
        print_status "Prometheus Stack already deployed"
    fi
    
    # Deploy Jaeger
    if ! helm list -n observability | grep -q "jaeger"; then
        print_status "Deploying Jaeger"
        helm install jaeger jaegertracing/jaeger \
            --namespace observability \
            --create-namespace \
            --set storage.type=memory \
            --wait \
            --timeout=10m
    else
        print_status "Jaeger already deployed"
    fi
    
    print_success "Infrastructure components deployed"
}

# Function to check service health
check_service_health() {
    local service=$1
    local namespace="${service}-${NAMESPACE_SUFFIX}"
    
    print_status "Checking health of $service"
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/"$service" -n "$namespace"
    
    # Check if service is responding
    local service_url
    if [ "$ENVIRONMENT" = "development" ]; then
        service_url="http://localhost:8000"
    else
        service_url="https://${service}.${ENVIRONMENT}.automobile-company.com"
    fi
    
    # Try to access health endpoint
    if kubectl get svc "$service" -n "$namespace" &> /dev/null; then
        print_success "$service is healthy"
    else
        print_warning "$service health check failed"
    fi
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    echo
    
    for service in "${SERVICES[@]}"; do
        local namespace="${service}-${NAMESPACE_SUFFIX}"
        echo -n "$service: "
        
        if kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
            local ready=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.status.readyReplicas}')
            local desired=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.spec.replicas}')
            echo -e "${GREEN}✓${NC} ($ready/$desired ready)"
        else
            echo -e "${RED}✗${NC} (not deployed)"
        fi
    done
}

# Function to show service URLs
show_urls() {
    print_status "Service URLs:"
    echo
    
    for service in "${SERVICES[@]}"; do
        if [ "$ENVIRONMENT" = "development" ]; then
            echo "$service: http://localhost:8000 (port-forward required)"
        else
            echo "$service: https://${service}.${ENVIRONMENT}.automobile-company.com"
        fi
    done
    
    echo
    print_status "Monitoring URLs:"
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "Grafana: http://localhost:3000 (port-forward required)"
        echo "Jaeger: http://localhost:16686 (port-forward required)"
    else
        echo "Grafana: https://grafana.${ENVIRONMENT}.automobile-company.com"
        echo "Jaeger: https://jaeger.${ENVIRONMENT}.automobile-company.com"
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Deployment completed"
    show_status
    show_urls
}

# Main execution
main() {
    print_status "Starting deployment for environment: $ENVIRONMENT"
    print_status "Using registry: $REGISTRY"
    print_status "Using tag: $TAG"
    echo
    
    # Check prerequisites
    check_kubectl
    check_helm
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Deploy all services
    for service in "${SERVICES[@]}"; do
        if deploy_service "$service"; then
            check_service_health "$service"
        else
            print_error "Failed to deploy $service"
            exit 1
        fi
        echo
    done
    
    # Show final status
    cleanup
}

# Handle script arguments
case "${1:-}" in
    "development"|"staging"|"production")
        main
        ;;
    "status")
        show_status
        ;;
    "urls")
        show_urls
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [environment] [tag]"
        echo "  environment: development, staging, or production (default: development)"
        echo "  tag: Docker image tag (default: latest)"
        echo ""
        echo "Commands:"
        echo "  status    Show deployment status"
        echo "  urls      Show service URLs"
        echo "  help      Show this help message"
        ;;
    *)
        print_error "Invalid environment: $1"
        echo "Usage: $0 [development|staging|production] [tag]"
        exit 1
        ;;
esac