# GCP Infrastructure Variables

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for single-zone resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = can(regex("^(dev|staging|production)$", var.environment))
    error_message = "Environment must be dev, staging, or production."
  }
}

# Network Configuration
variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "pods_cidr" {
  description = "CIDR block for Kubernetes pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for Kubernetes services"
  type        = string
  default     = "10.2.0.0/16"
}

variable "master_cidr" {
  description = "CIDR block for GKE master nodes"
  type        = string
  default     = "172.16.0.0/28"
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "master_authorized_networks" {
  description = "Networks authorized to access the cluster master"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = [
    {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  ]
}

# GKE Configuration
variable "kubernetes_version" {
  description = "Kubernetes version prefix for GKE cluster"
  type        = string
  default     = "1.28."
}

variable "node_zones" {
  description = "Zones for GKE node pools"
  type        = list(string)
  default     = ["us-central1-a", "us-central1-b", "us-central1-c"]
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "disk_size_gb" {
  description = "Disk size for GKE nodes (GB)"
  type        = number
  default     = 50
  
  validation {
    condition     = var.disk_size_gb >= 20 && var.disk_size_gb <= 1000
    error_message = "Disk size must be between 20 and 1000 GB."
  }
}

variable "node_count" {
  description = "Initial number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "min_node_count" {
  description = "Minimum number of nodes in the node pool"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes in the node pool"
  type        = number
  default     = 10
}

variable "use_preemptible_nodes" {
  description = "Use preemptible nodes for cost optimization"
  type        = bool
  default     = false
}

variable "enable_binary_authorization" {
  description = "Enable binary authorization for enhanced security"
  type        = bool
  default     = true
}

# Cluster Autoscaling
variable "cluster_autoscaling" {
  description = "Cluster autoscaling configuration"
  type = object({
    min_cpu_cores = number
    max_cpu_cores = number
    min_memory_gb = number
    max_memory_gb = number
  })
  default = {
    min_cpu_cores = 4
    max_cpu_cores = 100
    min_memory_gb = 8
    max_memory_gb = 400
  }
}

# Cloud SQL Configuration
variable "use_cloud_sql" {
  description = "Whether to create Cloud SQL instance"
  type        = bool
  default     = false
}

variable "postgres_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-f1-micro"
}

variable "postgres_disk_size" {
  description = "Cloud SQL disk size (GB)"
  type        = number
  default     = 20
}

variable "postgres_max_disk_size" {
  description = "Cloud SQL maximum disk size (GB)"
  type        = number
  default     = 100
}

# Redis Configuration
variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "STANDARD_HA"
  
  validation {
    condition     = can(regex("^(BASIC|STANDARD_HA)$", var.redis_tier))
    error_message = "Redis tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size_gb" {
  description = "Redis memory size (GB)"
  type        = number
  default     = 2
  
  validation {
    condition     = var.redis_memory_size_gb >= 1 && var.redis_memory_size_gb <= 300
    error_message = "Redis memory size must be between 1 and 300 GB."
  }
}

variable "redis_reserved_ip_range" {
  description = "Reserved IP range for Redis instance"
  type        = string
  default     = "10.3.0.0/29"
}

# Environment-specific configurations
variable "environment_configs" {
  description = "Environment-specific configurations"
  type = map(object({
    node_count         = number
    min_node_count     = number
    max_node_count     = number
    machine_type       = string
    redis_memory_size_gb = number
    use_preemptible_nodes = bool
  }))
  
  default = {
    dev = {
      node_count           = 1
      min_node_count       = 1
      max_node_count       = 3
      machine_type         = "e2-medium"
      redis_memory_size_gb = 1
      use_preemptible_nodes = true
    }
    staging = {
      node_count           = 2
      min_node_count       = 1
      max_node_count       = 5
      machine_type         = "e2-standard-2"
      redis_memory_size_gb = 1
      use_preemptible_nodes = false
    }
    production = {
      node_count           = 3
      min_node_count       = 2
      max_node_count       = 20
      machine_type         = "e2-standard-4"
      redis_memory_size_gb = 2
      use_preemptible_nodes = false
    }
  }
}

# Tags
variable "additional_labels" {
  description = "Additional labels to apply to all resources"
  type        = map(string)
  default     = {}
}

# Local values
locals {
  # Get environment-specific config
  env_config = var.environment_configs[var.environment]
  
  # Common labels
  common_labels = merge(
    {
      project     = "agentical"
      environment = var.environment
      managed-by  = "terraform"
      owner       = "devqai"
      application = "agentical-multi-agent-framework"
    },
    var.additional_labels
  )
  
  # Resource naming
  name_prefix = "agentical-${var.environment}"
}