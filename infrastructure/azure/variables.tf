# Azure Infrastructure Variables

variable "location" {
  description = "Azure region for deployment"
  type        = string
  default     = "East US"
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
variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aks_subnet_address_prefix" {
  description = "Address prefix for AKS subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "database_subnet_address_prefix" {
  description = "Address prefix for database subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "service_cidr" {
  description = "CIDR range for Kubernetes services"
  type        = string
  default     = "10.1.0.0/16"
}

variable "dns_service_ip" {
  description = "IP address for Kubernetes DNS service"
  type        = string
  default     = "10.1.0.10"
}

# AKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for AKS cluster"
  type        = string
  default     = "1.28.3"
}

variable "vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "os_disk_size_gb" {
  description = "OS disk size for AKS nodes (GB)"
  type        = number
  default     = 50
  
  validation {
    condition     = var.os_disk_size_gb >= 30 && var.os_disk_size_gb <= 1024
    error_message = "OS disk size must be between 30 and 1024 GB."
  }
}

variable "node_count" {
  description = "Initial number of nodes in the default node pool"
  type        = number
  default     = 3
}

variable "min_node_count" {
  description = "Minimum number of nodes in the default node pool"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes in the default node pool"
  type        = number
  default     = 10
}

variable "max_pods_per_node" {
  description = "Maximum number of pods per node"
  type        = number
  default     = 30
}

variable "enable_private_cluster" {
  description = "Enable private cluster configuration"
  type        = bool
  default     = true
}

variable "admin_group_object_ids" {
  description = "Azure AD group object IDs for cluster admin access"
  type        = list(string)
  default     = []
}

# Compute Node Pool Configuration
variable "compute_vm_size" {
  description = "VM size for compute-intensive node pool"
  type        = string
  default     = "Standard_D8s_v3"
}

variable "compute_node_count" {
  description = "Initial number of nodes in compute node pool"
  type        = number
  default     = 1
}

variable "compute_min_node_count" {
  description = "Minimum number of nodes in compute node pool"
  type        = number
  default     = 0
}

variable "compute_max_node_count" {
  description = "Maximum number of nodes in compute node pool"
  type        = number
  default     = 5
}

# Container Registry Configuration
variable "create_acr" {
  description = "Whether to create Azure Container Registry"
  type        = bool
  default     = true
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Premium"
  
  validation {
    condition     = can(regex("^(Basic|Standard|Premium)$", var.acr_sku))
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

variable "acr_georeplication_locations" {
  description = "Locations for ACR geo-replication"
  type        = list(string)
  default     = ["West US"]
}

# Database Configuration
variable "use_azure_database" {
  description = "Whether to create Azure Database for PostgreSQL"
  type        = bool
  default     = false
}

variable "postgres_admin_username" {
  description = "Administrator username for PostgreSQL"
  type        = string
  default     = "agentical_admin"
}

variable "postgres_admin_password" {
  description = "Administrator password for PostgreSQL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "postgres_sku_name" {
  description = "SKU name for PostgreSQL flexible server"
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "postgres_storage_mb" {
  description = "Storage size for PostgreSQL (MB)"
  type        = number
  default     = 32768
}

variable "postgres_storage_tier" {
  description = "Storage tier for PostgreSQL"
  type        = string
  default     = "P30"
}

variable "postgres_backup_retention_days" {
  description = "Backup retention period for PostgreSQL (days)"
  type        = number
  default     = 7
}

variable "postgres_geo_redundant_backup_enabled" {
  description = "Enable geo-redundant backup for PostgreSQL"
  type        = bool
  default     = false
}

# Redis Configuration
variable "redis_capacity" {
  description = "Redis cache capacity"
  type        = number
  default     = 2
}

variable "redis_family" {
  description = "Redis cache family"
  type        = string
  default     = "C"
}

variable "redis_sku_name" {
  description = "Redis cache SKU"
  type        = string
  default     = "Standard"
  
  validation {
    condition     = can(regex("^(Basic|Standard|Premium)$", var.redis_sku_name))
    error_message = "Redis SKU must be Basic, Standard, or Premium."
  }
}

variable "redis_maxmemory_reserved" {
  description = "Redis maxmemory reserved setting"
  type        = number
  default     = 125
}

variable "redis_maxmemory_delta" {
  description = "Redis maxmemory delta setting"
  type        = number
  default     = 125
}

# Storage Configuration
variable "storage_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "GRS"
  
  validation {
    condition     = can(regex("^(LRS|GRS|RAGRS|ZRS|GZRS|RAGZRS)$", var.storage_replication_type))
    error_message = "Storage replication type must be LRS, GRS, RAGRS, ZRS, GZRS, or RAGZRS."
  }
}

# Application Gateway Configuration
variable "create_application_gateway" {
  description = "Whether to create Application Gateway for ingress"
  type        = bool
  default     = false
}

# Monitoring Configuration
variable "log_retention_days" {
  description = "Log Analytics workspace retention period (days)"
  type        = number
  default     = 30
  
  validation {
    condition = contains([
      7, 30, 60, 90, 120, 180, 270, 365, 550, 730
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid Log Analytics retention period."
  }
}

# Environment-specific configurations
variable "environment_configs" {
  description = "Environment-specific configurations"
  type = map(object({
    node_count               = number
    min_node_count          = number
    max_node_count          = number
    vm_size                 = string
    redis_capacity          = number
    log_retention_days      = number
    enable_private_cluster  = bool
  }))
  
  default = {
    dev = {
      node_count              = 1
      min_node_count         = 1
      max_node_count         = 3
      vm_size                = "Standard_B2s"
      redis_capacity         = 1
      log_retention_days     = 7
      enable_private_cluster = false
    }
    staging = {
      node_count              = 2
      min_node_count         = 1
      max_node_count         = 5
      vm_size                = "Standard_D2s_v3"
      redis_capacity         = 1
      log_retention_days     = 30
      enable_private_cluster = true
    }
    production = {
      node_count              = 3
      min_node_count         = 2
      max_node_count         = 20
      vm_size                = "Standard_D4s_v3"
      redis_capacity         = 2
      log_retention_days     = 90
      enable_private_cluster = true
    }
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Local values
locals {
  # Get environment-specific config
  env_config = var.environment_configs[var.environment]
  
  # Common tags
  common_tags = merge(
    {
      Project     = "agentical"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "devqai"
      Application = "agentical-multi-agent-framework"
    },
    var.additional_tags
  )
  
  # Resource naming
  name_prefix = "agentical-${var.environment}"
}