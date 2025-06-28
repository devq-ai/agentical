# AWS Infrastructure for Agentical
# Terraform configuration for production deployment

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
    bucket  = "agentical-terraform-state"
    key     = "agentical/terraform.tfstate"
    region  = "us-west-2"
    encrypt = true
    
    dynamodb_table = "agentical-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "agentical"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "devqai"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Configuration
resource "aws_vpc" "agentical_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "agentical-vpc-${var.environment}"
    "kubernetes.io/cluster/agentical-${var.environment}" = "shared"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "agentical_igw" {
  vpc_id = aws_vpc.agentical_vpc.id
  
  tags = {
    Name = "agentical-igw-${var.environment}"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = var.public_subnet_count
  
  vpc_id                  = aws_vpc.agentical_vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "agentical-public-subnet-${count.index + 1}-${var.environment}"
    "kubernetes.io/cluster/agentical-${var.environment}" = "shared"
    "kubernetes.io/role/elb" = "1"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = var.private_subnet_count
  
  vpc_id            = aws_vpc.agentical_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + var.public_subnet_count)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "agentical-private-subnet-${count.index + 1}-${var.environment}"
    "kubernetes.io/cluster/agentical-${var.environment}" = "owned"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  count = var.private_subnet_count
  domain = "vpc"
  
  tags = {
    Name = "agentical-nat-eip-${count.index + 1}-${var.environment}"
  }
  
  depends_on = [aws_internet_gateway.agentical_igw]
}

resource "aws_nat_gateway" "agentical_nat" {
  count = var.private_subnet_count
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = {
    Name = "agentical-nat-${count.index + 1}-${var.environment}"
  }
  
  depends_on = [aws_internet_gateway.agentical_igw]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.agentical_vpc.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.agentical_igw.id
  }
  
  tags = {
    Name = "agentical-public-rt-${var.environment}"
  }
}

resource "aws_route_table" "private" {
  count  = var.private_subnet_count
  vpc_id = aws_vpc.agentical_vpc.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.agentical_nat[count.index].id
  }
  
  tags = {
    Name = "agentical-private-rt-${count.index + 1}-${var.environment}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = var.public_subnet_count
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = var.private_subnet_count
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "eks_cluster" {
  name_prefix = "agentical-eks-cluster-${var.environment}"
  vpc_id      = aws_vpc.agentical_vpc.id
  
  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "agentical-eks-cluster-sg-${var.environment}"
  }
}

resource "aws_security_group" "eks_nodes" {
  name_prefix = "agentical-eks-nodes-${var.environment}"
  vpc_id      = aws_vpc.agentical_vpc.id
  
  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }
  
  ingress {
    from_port       = 1025
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "agentical-eks-nodes-sg-${var.environment}"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "agentical" {
  name     = "agentical-${var.environment}"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version
  
  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    security_group_ids      = [aws_security_group.eks_cluster.id]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.allowed_cidr_blocks
  }
  
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  
  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_service_policy,
    aws_cloudwatch_log_group.eks_cluster,
  ]
  
  tags = {
    Name = "agentical-eks-${var.environment}"
  }
}

# EKS Node Group
resource "aws_eks_node_group" "agentical" {
  cluster_name    = aws_eks_cluster.agentical.name
  node_group_name = "agentical-nodes-${var.environment}"
  node_role_arn   = aws_iam_role.eks_node_group.arn
  subnet_ids      = aws_subnet.private[*].id
  
  capacity_type  = var.node_capacity_type
  instance_types = var.node_instance_types
  ami_type       = var.node_ami_type
  disk_size      = var.node_disk_size
  
  scaling_config {
    desired_size = var.node_desired_count
    max_size     = var.node_max_count
    min_size     = var.node_min_count
  }
  
  update_config {
    max_unavailable = 1
  }
  
  remote_access {
    ec2_ssh_key = var.ec2_key_pair_name
    source_security_group_ids = [aws_security_group.eks_nodes.id]
  }
  
  labels = {
    Environment = var.environment
    NodeGroup   = "agentical-nodes"
  }
  
  tags = {
    Name = "agentical-node-group-${var.environment}"
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}

# KMS Key for EKS
resource "aws_kms_key" "eks" {
  description             = "KMS key for Agentical EKS cluster encryption"
  deletion_window_in_days = var.kms_deletion_window
  
  tags = {
    Name = "agentical-eks-kms-${var.environment}"
  }
}

resource "aws_kms_alias" "eks" {
  name          = "alias/agentical-eks-${var.environment}"
  target_key_id = aws_kms_key.eks.key_id
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/agentical-${var.environment}/cluster"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.eks.arn
  
  tags = {
    Name = "agentical-eks-logs-${var.environment}"
  }
}

# RDS for SurrealDB alternative (optional)
resource "aws_db_subnet_group" "agentical" {
  count = var.use_rds ? 1 : 0
  
  name       = "agentical-db-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "agentical-db-subnet-group-${var.environment}"
  }
}

resource "aws_security_group" "rds" {
  count = var.use_rds ? 1 : 0
  
  name_prefix = "agentical-rds-${var.environment}"
  vpc_id      = aws_vpc.agentical_vpc.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }
  
  tags = {
    Name = "agentical-rds-sg-${var.environment}"
  }
}

# ElastiCache for Redis
resource "aws_elasticache_subnet_group" "agentical" {
  name       = "agentical-cache-subnet-${var.environment}"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "agentical-cache-subnet-group-${var.environment}"
  }
}

resource "aws_security_group" "elasticache" {
  name_prefix = "agentical-elasticache-${var.environment}"
  vpc_id      = aws_vpc.agentical_vpc.id
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }
  
  tags = {
    Name = "agentical-elasticache-sg-${var.environment}"
  }
}

resource "aws_elasticache_replication_group" "agentical" {
  description          = "Agentical Redis cluster"
  replication_group_id = "agentical-redis-${var.environment}"
  
  port                = 6379
  parameter_group_name = "default.redis7"
  node_type           = var.redis_node_type
  num_cache_clusters  = var.redis_num_nodes
  
  subnet_group_name  = aws_elasticache_subnet_group.agentical.name
  security_group_ids = [aws_security_group.elasticache.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token
  
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"
  
  auto_minor_version_upgrade = true
  
  tags = {
    Name = "agentical-redis-${var.environment}"
  }
}

# Application Load Balancer
resource "aws_lb" "agentical" {
  name               = "agentical-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
  
  enable_deletion_protection = var.environment == "production"
  
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "agentical-alb"
    enabled = true
  }
  
  tags = {
    Name = "agentical-alb-${var.environment}"
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "agentical-alb-${var.environment}"
  vpc_id      = aws_vpc.agentical_vpc.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "agentical-alb-sg-${var.environment}"
  }
}

# S3 Bucket for ALB Logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "agentical-alb-logs-${var.environment}-${random_string.bucket_suffix.result}"
  force_destroy = var.environment != "production"
  
  tags = {
    Name = "agentical-alb-logs-${var.environment}"
  }
}

resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  policy = data.aws_iam_policy_document.alb_logs.json
}

data "aws_iam_policy_document" "alb_logs" {
  statement {
    effect = "Allow"
    
    principals {
      type        = "AWS"
      identifiers = [data.aws_elb_service_account.main.arn]
    }
    
    actions = ["s3:PutObject"]
    
    resources = ["${aws_s3_bucket.alb_logs.arn}/*"]
  }
}

data "aws_elb_service_account" "main" {}

resource "random_string" "bucket_suffix" {
  length  = 8
  upper   = false
  special = false
}

# Route53 Hosted Zone (if managing DNS)
resource "aws_route53_zone" "agentical" {
  count = var.create_route53_zone ? 1 : 0
  
  name = var.domain_name
  
  tags = {
    Name = "agentical-zone-${var.environment}"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "agentical" {
  count = var.create_acm_certificate ? 1 : 0
  
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = {
    Name = "agentical-cert-${var.environment}"
  }
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.agentical.endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.agentical.name
}

output "cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = aws_eks_cluster.agentical.certificate_authority[0].data
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_replication_group.agentical.configuration_endpoint_address
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.agentical_vpc.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}