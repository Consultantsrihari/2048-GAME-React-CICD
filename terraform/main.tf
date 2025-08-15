terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket = "automobile-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.cluster.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# Data sources
data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "cluster" {
  name = var.cluster_name
}

# Local values
locals {
  common_tags = {
    Project     = "automobile-platform"
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  services = [
    "auth-api",
    "users-api",
    "vehicles-api",
    "orders-api",
    "payments-api",
    "inventory-api",
    "telemetry-api",
    "geofence-api",
    "notifications-api",
    "billing-api",
    "reports-api",
    "dealer-portal"
  ]
}

# Namespaces for each microservice
resource "kubernetes_namespace" "service_namespaces" {
  for_each = toset(local.services)

  metadata {
    name = "${each.key}-${var.environment}"
    labels = merge(local.common_tags, {
      service = each.key
    })
  }
}

# Service accounts for each microservice
resource "kubernetes_service_account" "service_accounts" {
  for_each = toset(local.services)

  metadata {
    name      = "${each.key}-sa"
    namespace = kubernetes_namespace.service_namespaces[each.key].metadata[0].name
    labels = merge(local.common_tags, {
      service = each.key
    })
  }
}

# RBAC - Role for each service
resource "kubernetes_role" "service_roles" {
  for_each = toset(local.services)

  metadata {
    name      = "${each.key}-role"
    namespace = kubernetes_namespace.service_namespaces[each.key].metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services", "endpoints"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "replicasets"]
    verbs      = ["get", "list", "watch"]
  }
}

# RBAC - RoleBinding for each service
resource "kubernetes_role_binding" "service_role_bindings" {
  for_each = toset(local.services)

  metadata {
    name      = "${each.key}-role-binding"
    namespace = kubernetes_namespace.service_namespaces[each.key].metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.service_roles[each.key].metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.service_accounts[each.key].metadata[0].name
    namespace = kubernetes_namespace.service_namespaces[each.key].metadata[0].name
  }
}

# Network Policies for each service
resource "kubernetes_network_policy" "service_network_policies" {
  for_each = toset(local.services)

  metadata {
    name      = "${each.key}-network-policy"
    namespace = kubernetes_namespace.service_namespaces[each.key].metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = each.key
      }
    }

    policy_types = ["Ingress", "Egress"]

    ingress {
      from {
        namespace_selector {
          match_labels = {
            name = "ingress-nginx"
          }
        }
      }
      
      # Allow inter-service communication
      from {
        namespace_selector {
          match_labels = {
            Project = "automobile-platform"
          }
        }
      }
    }

    egress {
      # Allow DNS resolution
      to {
        namespace_selector {
          match_labels = {
            name = "kube-system"
          }
        }
      }
      ports {
        port     = "53"
        protocol = "UDP"
      }
    }

    egress {
      # Allow inter-service communication
      to {
        namespace_selector {
          match_labels = {
            Project = "automobile-platform"
          }
        }
      }
    }

    egress {
      # Allow external HTTPS traffic
      ports {
        port     = "443"
        protocol = "TCP"
      }
    }
  }
}

# ConfigMaps for common configuration
resource "kubernetes_config_map" "common_config" {
  metadata {
    name      = "common-config"
    namespace = "default"
  }

  data = {
    LOG_LEVEL   = var.log_level
    ENVIRONMENT = var.environment
    AWS_REGION  = var.aws_region
  }
}

# Secrets for sensitive data
resource "kubernetes_secret" "jwt_secret" {
  metadata {
    name      = "jwt-secret"
    namespace = kubernetes_namespace.service_namespaces["auth-api"].metadata[0].name
  }

  data = {
    jwt-secret = var.jwt_secret
  }

  type = "Opaque"
}

# Install NGINX Ingress Controller
resource "helm_release" "nginx_ingress" {
  name       = "nginx-ingress"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "ingress-nginx"
  version    = "4.7.1"

  create_namespace = true

  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }

  set {
    name  = "controller.metrics.enabled"
    value = "true"
  }
}

# Install cert-manager for TLS certificates
resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  version    = "v1.12.0"

  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }
}

# ClusterIssuer for Let's Encrypt
resource "kubernetes_manifest" "letsencrypt_issuer" {
  depends_on = [helm_release.cert_manager]

  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = "letsencrypt-prod"
    }
    spec = {
      acme = {
        server = "https://acme-v02.api.letsencrypt.org/directory"
        email  = var.letsencrypt_email
        privateKeySecretRef = {
          name = "letsencrypt-prod"
        }
        solvers = [{
          http01 = {
            ingress = {
              class = "nginx"
            }
          }
        }]
      }
    }
  }
}