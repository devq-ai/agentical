# AWS Infrastructure Variables

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
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

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_count" {
  description = "Number of public subnets"
  type        = number
  default     = 3
  
  validation {
    condition     = var.public_subnet_count >= 2 && var.public_subnet_count <= 6
    error_message = "Public subnet count must be between 2 and 6."
  }
}

variable "private_subnet_count" {
  description = "Number of private subnets"
  type        = number
  default     = 3
  
  validation {
    condition     = var.private_subnet_count >= 2 && var.private_subnet_count <= 6
    error_message = "Private subnet count must be between 2 and 6."
  }
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access EKS API"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "node_capacity_type" {
  description = "Capacity type for EKS nodes (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"
  
  validation {
    condition     = can(regex("^(ON_DEMAND|SPOT)$", var.node_capacity_type))
    error_message = "Node capacity type must be ON_DEMAND or SPOT."
  }
}

variable "node_instance_types" {
  description = "Instance types for EKS worker nodes"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

variable "node_ami_type" {
  description = "AMI type for EKS worker nodes"
  type        = string
  default     = "AL2_x86_64"
}

variable "node_disk_size" {
  description = "Disk size for EKS worker nodes (GB)"
  type        = number
  default     = 50
  
  validation {
    condition     = var.node_disk_size >= 20 && var.node_disk_size <= 1000
    error_message = "Node disk size must be between 20 and 1000 GB."
  }
}

variable "node_desired_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "node_min_count" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "node_max_count" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "ec2_key_pair_name" {
  description = "EC2 Key Pair name for SSH access to nodes"
  type        = string
  default     = ""
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 2
  
  validation {
    condition     = var.redis_num_nodes >= 1 && var.redis_num_nodes <= 6
    error_message = "Redis node count must be between 1 and 6."
  }
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  default     = ""
  sensitive   = true
}

# RDS Configuration (optional)
variable "use_rds" {
  description = "Whether to create RDS instance"
  type        = bool
  default     = false
}

variable "rds_instance_type" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage (GB)"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum allocated storage (GB)"
  type        = number
  default     = 100
}

variable "rds_backup_retention_period" {
  description = "RDS backup retention period (days)"
  type        = number
  default     = 7
}

# Security Configuration
variable "kms_deletion_window" {
  description = "KMS key deletion window (days)"
  type        = number
  default     = 7
  
  validation {
    condition     = var.kms_deletion_window >= 7 && var.kms_deletion_window <= 30
    error_message = "KMS deletion window must be between 7 and 30 days."
  }
}

# Monitoring Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention period (days)"
  type        = number
  default     = 14
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

# DNS Configuration
variable "create_route53_zone" {
  description = "Whether to create Route53 hosted zone"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "agentical.example.com"
}

variable "create_acm_certificate" {
  description = "Whether to create ACM certificate"
  type        = bool
  default     = false
}

# Environment-specific configurations
variable "environment_configs" {
  description = "Environment-specific configurations"
  type = map(object({
    node_desired_count = number
    node_min_count     = number
    node_max_count     = number
    redis_num_nodes    = number
    log_retention_days = number
  }))
  
  default = {
    dev = {
      node_desired_count = 1
      node_min_count     = 1
      node_max_count     = 3
      redis_num_nodes    = 1
      log_retention_days = 7
    }
    staging = {
      node_desired_count = 2
      node_min_count     = 1
      node_max_count     = 5
      redis_num_nodes    = 1
      log_retention_days = 14
    }
    production = {
      node_desired_count = 3
      node_min_count     = 2
      node_max_count     = 20
      redis_num_nodes    = 2
      log_retention_days = 30
    }
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Cost optimization
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_max_price" {
  description = "Maximum price for spot instances"
  type        = string
  default     = ""
}

# Backup and disaster recovery
variable "enable_cross_region_backup" {
  description = "Enable cross-region backup"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "Backup region for disaster recovery"
  type        = string
  default     = "us-east-1"
}

# Compliance and security
variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config"
  type        = bool
  default     = true
}

variable "enable_guardduty" {
  description = "Enable GuardDuty"
  type        = bool
  default     = true
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
  
  # Subnet configuration
  public_subnet_cidrs  = [for i in range(var.public_subnet_count) : cidrsubnet(var.vpc_cidr, 8, i)]
  private_subnet_cidrs = [for i in range(var.private_subnet_count) : cidrsubnet(var.vpc_cidr, 8, i + var.public_subnet_count)]
}