# KMS Configuration for GCP
# Encryption keys for securing Agentical infrastructure

# KMS Key Ring
resource "google_kms_key_ring" "agentical" {
  name     = "agentical-keyring-${var.environment}"
  location = var.region
  
  depends_on = [google_project_service.kms_api]
}

# GKE Encryption Key
resource "google_kms_crypto_key" "gke_key" {
  name     = "agentical-gke-key-${var.environment}"
  key_ring = google_kms_key_ring.agentical.id
  purpose  = "ENCRYPT_DECRYPT"
  
  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
  
  rotation_period = "7776000s" # 90 days
  
  lifecycle {
    prevent_destroy = true
  }
}

# Storage Encryption Key
resource "google_kms_crypto_key" "storage_key" {
  name     = "agentical-storage-key-${var.environment}"
  key_ring = google_kms_key_ring.agentical.id
  purpose  = "ENCRYPT_DECRYPT"
  
  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
  
  rotation_period = "7776000s" # 90 days
  
  lifecycle {
    prevent_destroy = true
  }
}

# Cloud SQL Encryption Key
resource "google_kms_crypto_key" "sql_key" {
  count = var.use_cloud_sql ? 1 : 0
  
  name     = "agentical-sql-key-${var.environment}"
  key_ring = google_kms_key_ring.agentical.id
  purpose  = "ENCRYPT_DECRYPT"
  
  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
  
  rotation_period = "7776000s" # 90 days
  
  lifecycle {
    prevent_destroy = true
  }
}

# IAM binding for GKE service account to use encryption key
resource "google_kms_crypto_key_iam_binding" "gke_key_binding" {
  crypto_key_id = google_kms_crypto_key.gke_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  
  members = [
    "serviceAccount:service-${data.google_project.current.number}@container-engine-robot.iam.gserviceaccount.com",
  ]
}

# IAM binding for Compute Engine service account to use storage key
resource "google_kms_crypto_key_iam_binding" "storage_key_binding" {
  crypto_key_id = google_kms_crypto_key.storage_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  
  members = [
    "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com",
  ]
}

# IAM binding for Cloud SQL service account to use encryption key
resource "google_kms_crypto_key_iam_binding" "sql_key_binding" {
  count = var.use_cloud_sql ? 1 : 0
  
  crypto_key_id = google_kms_crypto_key.sql_key[0].id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  
  members = [
    "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloud-sql.iam.gserviceaccount.com",
  ]
}

# Get current project information
data "google_project" "current" {}

# Output KMS key information
output "gke_kms_key_id" {
  description = "GKE KMS key ID"
  value       = google_kms_crypto_key.gke_key.id
}

output "storage_kms_key_id" {
  description = "Storage KMS key ID"
  value       = google_kms_crypto_key.storage_key.id
}

output "sql_kms_key_id" {
  description = "Cloud SQL KMS key ID"
  value       = var.use_cloud_sql ? google_kms_crypto_key.sql_key[0].id : null
}