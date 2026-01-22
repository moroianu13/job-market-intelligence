# Terraform Configuration for AWS Deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "job-intelligence-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  default     = "job-market-intelligence"
}

# VPC and Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "${var.app_name}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name        = "${var.app_name}-public-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name        = "${var.app_name}-cluster"
    Environment = var.environment
  }
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name                 = var.app_name
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name        = var.app_name
    Environment = var.environment
  }
}

# S3 Bucket for Data Storage
resource "aws_s3_bucket" "data" {
  bucket = "${var.app_name}-data-${var.environment}"
  
  tags = {
    Name        = "${var.app_name}-data"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  
  rule {
    id     = "archive-old-snapshots"
    status = "Enabled"
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}

# RDS for Metadata (optional)
resource "aws_db_instance" "metadata" {
  identifier             = "${var.app_name}-metadata"
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  db_name                = "job_intelligence"
  username               = "admin"
  password               = random_password.db_password.result
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.app_name}-final-snapshot"
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  tags = {
    Name        = "${var.app_name}-metadata-db"
    Environment = var.environment
  }
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for Credentials
resource "aws_secretsmanager_secret" "adzuna_credentials" {
  name        = "${var.app_name}-adzuna-credentials"
  description = "Adzuna API credentials"
  
  tags = {
    Name        = "${var.app_name}-credentials"
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 30
  
  tags = {
    Name        = "${var.app_name}-logs"
    Environment = var.environment
  }
}

# EventBridge Rule for Scheduled Pipeline
resource "aws_cloudwatch_event_rule" "pipeline_schedule" {
  name                = "${var.app_name}-pipeline-schedule"
  description         = "Trigger pipeline execution weekly"
  schedule_expression = "cron(0 2 ? * MON *)"
  
  tags = {
    Name        = "${var.app_name}-pipeline-schedule"
    Environment = var.environment
  }
}

# Outputs
output "ecr_repository_url" {
  value       = aws_ecr_repository.app.repository_url
  description = "ECR repository URL"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.data.id
  description = "S3 bucket for data storage"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name"
}
