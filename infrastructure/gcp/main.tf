# GCP Infrastructure for Agentical
# Terraform configuration for Google Cloud Platform deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
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
  
  backend "gcs" {
    bucket = "agentical-terraform-state-gcp"
    prefix = "agentical/terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Data sources
data "google_client_config" "default" {}

data "google_container_engine_versions" "gke_version" {
  location = var.region
  version_prefix = var.kubernetes_version
}

# VPC Network
resource "google_compute_network" "agentical_vpc" {
  name                    = "agentical-vpc-${var.environment}"
  auto_create_subnetworks = false
  
  depends_on = [
    google_project_service.compute_api,
    google_project_service.container_api
  ]
}

# Subnet
resource "google_compute_subnetwork" "agentical_subnet" {
  name          = "agentical-subnet-${var.environment}"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.agentical_vpc.id
  
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = var.pods_cidr
  }
  
  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = var.services_cidr
  }
  
  private_ip_google_access = true
}

# Cloud Router for NAT
resource "google_compute_router" "agentical_router" {
  name    = "agentical-router-${var.environment}"
  region  = var.region
  network = google_compute_network.agentical_vpc.id
}

# Cloud NAT
resource "google_compute_router_nat" "agentical_nat" {
  name                               = "agentical-nat-${var.environment}"
  router                             = google_compute_router.agentical_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall Rules
resource "google_compute_firewall" "allow_internal" {
  name    = "agentical-allow-internal-${var.environment}"
  network = google_compute_network.agentical_vpc.id
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "agentical-allow-ssh-${var.environment}"
  network = google_compute_network.agentical_vpc.id
  
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  
  source_ranges = var.allowed_ssh_cidrs
  target_tags   = ["gke-node"]
}

resource "google_compute_firewall" "allow_https" {
  name    = "agentical-allow-https-${var.environment}"
  network = google_compute_network.agentical_vpc.id
  
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gke-node"]
}

# GKE Cluster
resource "google_container_cluster" "agentical" {
  name     = "agentical-gke-${var.environment}"
  location = var.region
  
  # Use regional cluster for high availability
  node_locations = var.node_zones
  
  # Network configuration
  network    = google_compute_network.agentical_vpc.id
  subnetwork = google_compute_subnetwork.agentical_subnet.id
  
  # IP allocation policy
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }
  
  # Network policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }
  
  # Addons configuration
  addons_config {
    http_load_balancing {
      disabled = false
    }
    
    horizontal_pod_autoscaling {
      disabled = false
    }
    
    network_policy_config {
      disabled = false
    }
    
    dns_cache_config {
      enabled = true
    }
  }
  
  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Security configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_cidr
    
    master_global_access_config {
      enabled = true
    }
  }
  
  # Master authorized networks
  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.master_authorized_networks
      content {
        cidr_block   = cidr_blocks.value.cidr_block
        display_name = cidr_blocks.value.display_name
      }
    }
  }
  
  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
  
  # Cluster autoscaling
  cluster_autoscaling {
    enabled = true
    
    resource_limits {
      resource_type = "cpu"
      minimum       = var.cluster_autoscaling.min_cpu_cores
      maximum       = var.cluster_autoscaling.max_cpu_cores
    }
    
    resource_limits {
      resource_type = "memory"
      minimum       = var.cluster_autoscaling.min_memory_gb
      maximum       = var.cluster_autoscaling.max_memory_gb
    }
    
    auto_provisioning_defaults {
      oauth_scopes = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/logging.write",
        "https://www.googleapis.com/auth/monitoring",
        "https://www.googleapis.com/auth/service.management.readonly",
        "https://www.googleapis.com/auth/servicecontrol",
        "https://www.googleapis.com/auth/trace.append",
      ]
    }
  }
  
  # Database encryption
  database_encryption {
    state    = "ENCRYPTED"
    key_name = google_kms_crypto_key.gke_key.id
  }
  
  # Binary authorization
  enable_binary_authorization = var.enable_binary_authorization
  
  # Shielded nodes
  enable_shielded_nodes = true
  
  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1
  
  depends_on = [
    google_project_service.container_api,
    google_project_service.compute_api,
  ]
}

# Primary Node Pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "agentical-node-pool-${var.environment}"
  location   = var.region
  cluster    = google_container_cluster.agentical.name
  
  node_count = var.node_count
  
  # Node configuration
  node_config {
    preemptible  = var.use_preemptible_nodes
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-ssd"
    
    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/trace.append",
    ]
    
    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
    
    # Labels
    labels = {
      environment = var.environment
      project     = "agentical"
      managed-by  = "terraform"
    }
    
    # Tags
    tags = ["gke-node", "agentical-${var.environment}"]
    
    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
  
  # Node pool autoscaling
  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }
  
  # Node pool management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# Cloud SQL for PostgreSQL (if needed)
resource "google_sql_database_instance" "agentical_postgres" {
  count = var.use_cloud_sql ? 1 : 0
  
  name             = "agentical-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = var.postgres_tier
    
    disk_autoresize       = true
    disk_autoresize_limit = var.postgres_max_disk_size
    disk_size             = var.postgres_disk_size
    disk_type             = "PD_SSD"
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.agentical_vpc.id
      require_ssl     = true
    }
    
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    
    maintenance_window {
      day          = 1
      hour         = 3
      update_track = "stable"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  deletion_protection = var.environment == "production"
  
  depends_on = [
    google_service_networking_connection.private_vpc_connection
  ]
}

# Cloud Memorystore for Redis
resource "google_redis_instance" "agentical_redis" {
  name           = "agentical-redis-${var.environment}"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  
  authorized_network = google_compute_network.agentical_vpc.id
  
  redis_version     = "REDIS_7_0"
  display_name      = "Agentical Redis ${var.environment}"
  reserved_ip_range = var.redis_reserved_ip_range
  
  auth_enabled   = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }
  
  persistence_config {
    persistence_mode    = "RDB"
    rdb_snapshot_period = "TWENTY_FOUR_HOURS"
    rdb_snapshot_start_time = "03:00"
  }
}

# Cloud Storage Buckets
resource "google_storage_bucket" "agentical_data" {
  name          = "agentical-data-${var.environment}-${random_string.bucket_suffix.result}"
  location      = var.region
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 7
      matches_storage_class = ["STANDARD"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "agentical_backups" {
  name          = "agentical-backups-${var.environment}-${random_string.bucket_suffix.result}"
  location      = var.region
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Load Balancer
resource "google_compute_global_address" "agentical_ip" {
  name = "agentical-ip-${var.environment}"
}

# Service networking for private services
resource "google_compute_global_address" "private_ip_address" {
  name          = "agentical-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.agentical_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.agentical_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Enable required APIs
resource "google_project_service" "compute_api" {
  service = "compute.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "container_api" {
  service = "container.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "sql_api" {
  service = "sqladmin.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "redis_api" {
  service = "redis.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "kms_api" {
  service = "cloudkms.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "logging_api" {
  service = "logging.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "monitoring_api" {
  service = "monitoring.googleapis.com"
  
  disable_dependent_services = true
}

resource "google_project_service" "servicenetworking_api" {
  service = "servicenetworking.googleapis.com"
  
  disable_dependent_services = true
}

# Random suffix for unique bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  upper   = false
  special = false
}

# Outputs
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.agentical.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.agentical.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.agentical.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.agentical_redis.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.agentical_redis.port
}

output "postgres_connection_name" {
  description = "Cloud SQL connection name"
  value       = var.use_cloud_sql ? google_sql_database_instance.agentical_postgres[0].connection_name : null
}

output "storage_bucket_name" {
  description = "Storage bucket name"
  value       = google_storage_bucket.agentical_data.name
}

output "backup_bucket_name" {
  description = "Backup bucket name"
  value       = google_storage_bucket.agentical_backups.name
}

output "load_balancer_ip" {
  description = "Load balancer IP address"
  value       = google_compute_global_address.agentical_ip.address
}