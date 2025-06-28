# Azure Key Vault Configuration
# Secure storage for secrets and encryption keys

# Key Vault
resource "azurerm_key_vault" "agentical" {
  name                = "agentical-kv-${var.environment}-${random_string.kv_suffix.result}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "premium"
  
  enabled_for_deployment          = true
  enabled_for_disk_encryption     = true
  enabled_for_template_deployment = true
  purge_protection_enabled        = var.environment == "production"
  soft_delete_retention_days      = 7
  
  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    
    virtual_network_subnet_ids = [
      azurerm_subnet.aks.id,
      azurerm_subnet.database.id
    ]
  }
  
  tags = local.common_tags
}

# Random suffix for Key Vault (names must be globally unique)
resource "random_string" "kv_suffix" {
  length  = 8
  upper   = false
  special = false
}

# Access policy for current user/service principal
resource "azurerm_key_vault_access_policy" "deployer" {
  key_vault_id = azurerm_key_vault.agentical.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id
  
  key_permissions = [
    "Backup", "Create", "Decrypt", "Delete", "Encrypt", "Get", "Import",
    "List", "Purge", "Recover", "Restore", "Sign", "UnwrapKey", "Update",
    "Verify", "WrapKey", "Release", "Rotate", "GetRotationPolicy", "SetRotationPolicy"
  ]
  
  secret_permissions = [
    "Backup", "Delete", "Get", "List", "Purge", "Recover", "Restore", "Set"
  ]
  
  certificate_permissions = [
    "Backup", "Create", "Delete", "DeleteIssuers", "Get", "GetIssuers",
    "Import", "List", "ListIssuers", "ManageContacts", "ManageIssuers",
    "Purge", "Recover", "Restore", "SetIssuers", "Update"
  ]
}

# Access policy for AKS Key Vault secrets provider
resource "azurerm_key_vault_access_policy" "aks_secrets_provider" {
  key_vault_id = azurerm_key_vault.agentical.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_kubernetes_cluster.agentical.key_vault_secrets_provider[0].secret_identity[0].object_id
  
  secret_permissions = [
    "Get"
  ]
  
  depends_on = [azurerm_kubernetes_cluster.agentical]
}

# User assigned identity for ACR encryption
resource "azurerm_user_assigned_identity" "acr" {
  count = var.create_acr ? 1 : 0
  
  name                = "agentical-acr-identity-${var.environment}"
  location            = azurerm_resource_group.agentical.location
  resource_group_name = azurerm_resource_group.agentical.name
  
  tags = local.common_tags
}

# Access policy for ACR encryption identity
resource "azurerm_key_vault_access_policy" "acr" {
  count = var.create_acr ? 1 : 0
  
  key_vault_id = azurerm_key_vault.agentical.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.acr[0].principal_id
  
  key_permissions = [
    "Get", "UnwrapKey", "WrapKey"
  ]
}

# Encryption keys
resource "azurerm_key_vault_key" "aks" {
  name         = "agentical-aks-key-${var.environment}"
  key_vault_id = azurerm_key_vault.agentical.id
  key_type     = "RSA"
  key_size     = 2048
  
  key_opts = [
    "decrypt", "encrypt", "sign", "unwrapKey", "verify", "wrapKey"
  ]
  
  rotation_policy {
    automatic {
      time_before_expiry = "P30D"
    }
    
    expire_after         = "P90D"
    notify_before_expiry = "P29D"
  }
  
  depends_on = [azurerm_key_vault_access_policy.deployer]
  
  tags = local.common_tags
}

resource "azurerm_key_vault_key" "storage" {
  name         = "agentical-storage-key-${var.environment}"
  key_vault_id = azurerm_key_vault.agentical.id
  key_type     = "RSA"
  key_size     = 2048
  
  key_opts = [
    "decrypt", "encrypt", "sign", "unwrapKey", "verify", "wrapKey"
  ]
  
  rotation_policy {
    automatic {
      time_before_expiry = "P30D"
    }
    
    expire_after         = "P90D"
    notify_before_expiry = "P29D"
  }
  
  depends_on = [azurerm_key_vault_access_policy.deployer]
  
  tags = local.common_tags
}

resource "azurerm_key_vault_key" "acr" {
  count = var.create_acr ? 1 : 0
  
  name         = "agentical-acr-key-${var.environment}"
  key_vault_id = azurerm_key_vault.agentical.id
  key_type     = "RSA"
  key_size     = 2048
  
  key_opts = [
    "decrypt", "encrypt", "sign", "unwrapKey", "verify", "wrapKey"
  ]
  
  rotation_policy {
    automatic {
      time_before_expiry = "P30D"
    }
    
    expire_after         = "P90D"
    notify_before_expiry = "P29D"
  }
  
  depends_on = [
    azurerm_key_vault_access_policy.deployer,
    azurerm_key_vault_access_policy.acr
  ]
  
  tags = local.common_tags
}

# Application secrets
resource "azurerm_key_vault_secret" "postgres_password" {
  count = var.use_azure_database ? 1 : 0
  
  name         = "postgres-admin-password"
  value        = var.postgres_admin_password
  key_vault_id = azurerm_key_vault.agentical.id
  
  depends_on = [azurerm_key_vault_access_policy.deployer]
  
  tags = local.common_tags
}

resource "azurerm_key_vault_secret" "redis_primary_key" {
  name         = "redis-primary-key"
  value        = azurerm_redis_cache.agentical.primary_access_key
  key_vault_id = azurerm_key_vault.agentical.id
  
  depends_on = [azurerm_key_vault_access_policy.deployer]
  
  tags = local.common_tags
}

resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.agentical.primary_connection_string
  key_vault_id = azurerm_key_vault.agentical.id
  
  depends_on = [azurerm_key_vault_access_policy.deployer]
  
  tags = local.common_tags
}

# Certificates for TLS
resource "azurerm_key_vault_certificate" "agentical_tls" {
  name         = "agentical-tls-cert"
  key_vault_id = azurerm_key_vault.agentical.id
  
  certificate_policy {
    issuer_parameters {
      name = "Self"
    }
    
    key_properties {
      exportable = true
      key_size   = 2048
      key_type   = "RSA"
      reuse_key  = true
    }
    
    lifetime_actions {
      action {
        action_type = "AutoRenew"
      }
      
      trigger {
        days_before_expiry = 30
      }
    }
    
    secret_properties {
      content_type = "application/x-pkcs12"
    }
    
    x509_certificate_properties {
      extended_key_usage = ["1.3.6.1.5.5.7.3.1"]
      
      key_usage = [
        "cRLSign",
        "dataEncipherment",
        "digitalSignature",
        "keyAgreement",
        "keyCertSign",
        "keyEncipherment",
      ]
      
      subject            = "CN=agentical-${var.environment}.local"
      validity_in_months = 12
      
      subject_alternative_names {
        dns_names = [
          "agentical-${var.environment}.local",
          "*.agentical-${var.environment}.local"
        ]
      }
    }
  }
  
  depends_on = [azurerm_key_vault_access_policy.deployer]
  
  tags = local.common_tags
}

# Output Key Vault information
output "key_vault_id" {
  description = "Key Vault ID"
  value       = azurerm_key_vault.agentical.id
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = azurerm_key_vault.agentical.vault_uri
}

output "aks_encryption_key_id" {
  description = "AKS encryption key ID"
  value       = azurerm_key_vault_key.aks.id
}

output "storage_encryption_key_id" {
  description = "Storage encryption key ID"
  value       = azurerm_key_vault_key.storage.id
}

output "acr_encryption_key_id" {
  description = "ACR encryption key ID"
  value       = var.create_acr ? azurerm_key_vault_key.acr[0].id : null
}