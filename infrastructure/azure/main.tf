# Azure Infrastructure for Agentical
# Terraform configuration for Microsoft Azure deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
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
  
  backend "azurerm" {
    resource_group_name  = "agentical-terraform-state"
    storage_account_name = "agenticalterraformstate"
    container_name       = "tfstate"
    key                  = "agentical/terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Data sources
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "agentical" {
  name     = "agentical-rg-${var.environment}"
  location = var.location
  
  tags = local.common_tags
}

# Virtual Network
resource "azurerm_virtual_network" "agentical" {
  name                = "agentical-vnet-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  address_space       = [var.vnet_address_space]
  
  tags = local.common_tags
}

# Subnet for AKS
resource "azurerm_subnet" "aks" {
  name                 = "agentical-aks-subnet-${var.environment}"
  resource_group_name  = azurerm_resource_group.agentical.name
  virtual_network_name = azurerm_virtual_network.agentical.name
  address_prefixes     = [var.aks_subnet_address_prefix]
}

# Subnet for Azure Database
resource "azurerm_subnet" "database" {
  name                 = "agentical-db-subnet-${var.environment}"
  resource_group_name  = azurerm_resource_group.agentical.name
  virtual_network_name = azurerm_virtual_network.agentical.name
  address_prefixes     = [var.database_subnet_address_prefix]
  
  delegation {
    name = "database_delegation"
    
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Private DNS Zone for PostgreSQL
resource "azurerm_private_dns_zone" "postgres" {
  count = var.use_azure_database ? 1 : 0
  
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.agentical.name
  
  tags = local.common_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  count = var.use_azure_database ? 1 : 0
  
  name                  = "agentical-postgres-dns-link-${var.environment}"
  resource_group_name   = azurerm_resource_group.agentical.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres[0].name
  virtual_network_id    = azurerm_virtual_network.agentical.id
  
  tags = local.common_tags
}

# Network Security Group
resource "azurerm_network_security_group" "aks" {
  name                = "agentical-aks-nsg-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  
  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  tags = local.common_tags
}

# Associate NSG with AKS subnet
resource "azurerm_subnet_network_security_group_association" "aks" {
  subnet_id                 = azurerm_subnet.aks.id
  network_security_group_id = azurerm_network_security_group.aks.id
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "agentical" {
  name                = "agentical-logs-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  
  tags = local.common_tags
}

# Container Insights Solution
resource "azurerm_log_analytics_solution" "container_insights" {
  solution_name         = "ContainerInsights"
  location              = azurerm_resource_group.agentical.location
  resource_group_name   = azurerm_resource_group.agentical.name
  workspace_resource_id = azurerm_log_analytics_workspace.agentical.id
  workspace_name        = azurerm_log_analytics_workspace.agentical.name
  
  plan {
    publisher = "Microsoft"
    product   = "OMSGallery/ContainerInsights"
  }
  
  tags = local.common_tags
}

# User Assigned Identity for AKS
resource "azurerm_user_assigned_identity" "aks" {
  name                = "agentical-aks-identity-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  
  tags = local.common_tags
}

# Role assignments for AKS identity
resource "azurerm_role_assignment" "aks_network_contributor" {
  scope                = azurerm_virtual_network.agentical.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  count = var.create_acr ? 1 : 0
  
  scope                = azurerm_container_registry.agentical[0].id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

# Azure Kubernetes Service
resource "azurerm_kubernetes_cluster" "agentical" {
  name                = "agentical-aks-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  dns_prefix          = "agentical-${var.environment}"
  kubernetes_version  = var.kubernetes_version
  
  # Default node pool
  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.vm_size
    os_disk_size_gb     = var.os_disk_size_gb
    vnet_subnet_id      = azurerm_subnet.aks.id
    max_pods            = var.max_pods_per_node
    enable_auto_scaling = true
    min_count           = var.min_node_count
    max_count           = var.max_node_count
    
    upgrade_settings {
      max_surge = "10%"
    }
  }
  
  # Identity configuration
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }
  
  # Network configuration
  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    dns_service_ip    = var.dns_service_ip
    service_cidr      = var.service_cidr
    load_balancer_sku = "standard"
  }
  
  # RBAC configuration
  azure_active_directory_role_based_access_control {
    managed                = true
    admin_group_object_ids = var.admin_group_object_ids
    azure_rbac_enabled     = true
  }
  
  # Monitoring
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.agentical.id
  }
  
  # Add-ons
  azure_policy_enabled = true
  
  # Auto-scaler profile
  auto_scaler_profile {
    balance_similar_node_groups      = true
    expander                         = "random"
    max_graceful_termination_sec     = 600
    max_node_provisioning_time       = "15m"
    max_unready_nodes                = 3
    max_unready_percentage           = 45
    new_pod_scale_up_delay           = "10s"
    scale_down_delay_after_add       = "10m"
    scale_down_delay_after_delete    = "10s"
    scale_down_delay_after_failure   = "3m"
    scale_down_unneeded              = "10m"
    scale_down_unready               = "20m"
    scale_down_utilization_threshold = 0.5
    scan_interval                    = "10s"
    skip_nodes_with_local_storage    = false
    skip_nodes_with_system_pods      = true
  }
  
  # Private cluster configuration
  private_cluster_enabled             = var.enable_private_cluster
  private_dns_zone_id                 = var.enable_private_cluster ? "System" : null
  private_cluster_public_fqdn_enabled = false
  
  # Key Vault secrets provider
  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }
  
  tags = local.common_tags
  
  depends_on = [
    azurerm_role_assignment.aks_network_contributor,
  ]
}

# Additional node pool for compute-intensive workloads
resource "azurerm_kubernetes_cluster_node_pool" "compute" {
  name                  = "compute"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.agentical.id
  vm_size               = var.compute_vm_size
  node_count            = var.compute_node_count
  os_disk_size_gb       = var.os_disk_size_gb
  vnet_subnet_id        = azurerm_subnet.aks.id
  max_pods              = var.max_pods_per_node
  enable_auto_scaling   = true
  min_count             = var.compute_min_node_count
  max_count             = var.compute_max_node_count
  
  node_labels = {
    "workload-type" = "compute-intensive"
  }
  
  node_taints = [
    "workload-type=compute-intensive:NoSchedule"
  ]
  
  tags = local.common_tags
}

# Azure Container Registry
resource "azurerm_container_registry" "agentical" {
  count = var.create_acr ? 1 : 0
  
  name                = "agenticalacr${var.environment}${random_string.acr_suffix.result}"
  resource_group_name = azurerm_resource_group.agentical.name
  location            = azurerm_resource_group.agentical.location
  sku                 = var.acr_sku
  admin_enabled       = false
  
  identity {
    type = "SystemAssigned"
  }
  
  encryption {
    enabled            = true
    key_vault_key_id   = azurerm_key_vault_key.acr[0].id
    identity_client_id = azurerm_user_assigned_identity.acr[0].client_id
  }
  
  dynamic "georeplications" {
    for_each = var.acr_georeplication_locations
    content {
      location                = georeplications.value
      zone_redundancy_enabled = true
    }
  }
  
  tags = local.common_tags
  
  depends_on = [
    azurerm_key_vault_access_policy.acr
  ]
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "agentical" {
  count = var.use_azure_database ? 1 : 0
  
  name                   = "agentical-postgres-${var.environment}"
  resource_group_name    = azurerm_resource_group.agentical.name
  location               = azurerm_resource_group.agentical.location
  version                = "15"
  delegated_subnet_id    = azurerm_subnet.database.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres[0].id
  administrator_login    = var.postgres_admin_username
  administrator_password = var.postgres_admin_password
  zone                   = "1"
  
  storage_mb   = var.postgres_storage_mb
  storage_tier = var.postgres_storage_tier
  
  sku_name = var.postgres_sku_name
  
  backup_retention_days        = var.postgres_backup_retention_days
  geo_redundant_backup_enabled = var.postgres_geo_redundant_backup_enabled
  
  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"
  }
  
  maintenance_window {
    day_of_week  = 0
    start_hour   = 8
    start_minute = 0
  }
  
  tags = local.common_tags
  
  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "agentical" {
  name                = "agentical-redis-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  capacity            = var.redis_capacity
  family              = var.redis_family
  sku_name            = var.redis_sku_name
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  
  subnet_id = var.redis_sku_name == "Premium" ? azurerm_subnet.database.id : null
  
  redis_configuration {
    enable_authentication           = true
    maxmemory_reserved              = var.redis_maxmemory_reserved
    maxmemory_delta                 = var.redis_maxmemory_delta
    maxmemory_policy                = "allkeys-lru"
    rdb_backup_enabled              = var.redis_sku_name == "Premium"
    rdb_backup_frequency            = var.redis_sku_name == "Premium" ? 60 : null
    rdb_backup_max_snapshot_count   = var.redis_sku_name == "Premium" ? 1 : null
    rdb_storage_connection_string   = var.redis_sku_name == "Premium" ? azurerm_storage_account.agentical.primary_blob_connection_string : null
  }
  
  tags = local.common_tags
}

# Storage Account
resource "azurerm_storage_account" "agentical" {
  name                     = "agenticalstore${var.environment}${random_string.storage_suffix.result}"
  resource_group_name      = azurerm_resource_group.agentical.name
  location                 = azurerm_resource_group.agentical.location
  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type
  
  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true
    
    delete_retention_policy {
      days = 30
    }
    
    container_delete_retention_policy {
      days = 7
    }
  }
  
  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.aks.id]
    bypass                     = ["AzureServices"]
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = local.common_tags
}

# Storage containers
resource "azurerm_storage_container" "agentical_data" {
  name                  = "agentical-data"
  storage_account_name  = azurerm_storage_account.agentical.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "agentical_backups" {
  name                  = "agentical-backups"
  storage_account_name  = azurerm_storage_account.agentical.name
  container_access_type = "private"
}

# Application Gateway (if using ingress)
resource "azurerm_public_ip" "agentical" {
  count = var.create_application_gateway ? 1 : 0
  
  name                = "agentical-appgw-ip-${var.environment}"
  resource_group_name = azurerm_resource_group.agentical.name
  location            = azurerm_resource_group.agentical.location
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = local.common_tags
}

# Random strings for unique naming
resource "random_string" "acr_suffix" {
  length  = 8
  upper   = false
  special = false
}

resource "random_string" "storage_suffix" {
  length  = 8
  upper   = false
  special = false
}

# Outputs
output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.agentical.name
}

output "cluster_endpoint" {
  description = "AKS cluster endpoint"
  value       = azurerm_kubernetes_cluster.agentical.kube_config[0].host
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "AKS cluster CA certificate"
  value       = azurerm_kubernetes_cluster.agentical.kube_config[0].cluster_ca_certificate
  sensitive   = true
}

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.agentical.name
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = azurerm_redis_cache.agentical.hostname
}

output "redis_primary_access_key" {
  description = "Redis primary access key"
  value       = azurerm_redis_cache.agentical.primary_access_key
  sensitive   = true
}

output "postgres_fqdn" {
  description = "PostgreSQL FQDN"
  value       = var.use_azure_database ? azurerm_postgresql_flexible_server.agentical[0].fqdn : null
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.agentical.name
}

output "acr_login_server" {
  description = "ACR login server"
  value       = var.create_acr ? azurerm_container_registry.agentical[0].login_server : null
}