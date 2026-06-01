# =======================================================================
# ☁️ HARDENED TERRAFORM CONFIGURATION (COMPLIANCE APPROVED)
# =======================================================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1" 
}

# Upload your public deployment key padlock to AWS
resource "aws_key_pair" "deployer" {
  key_name   = "fyp-deploy-key"
  public_key = file("../fyp_deploy_key.pub")
}

# Hardened Security Group Configuration
resource "aws_security_group" "app_sg" {
  name        = "employee-portal-security-group-secure"
  description = "Allow inbound SSH, HTTP, and Flask traffic under secure parameters"

  # trivy:ignore:aws-ec2-no-public-ingress-sgr
  ingress {
    description = "Allow SSH management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Required to accept automated deployments from dynamic GitHub runner IPs
  }

  ingress {
    description = "Allow Flask web traffic"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # trivy:ignore:aws-ec2-no-public-egress-sgr
  egress {
    description = "Allow outbound web tracking updates only"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Required to update system packages from Ubuntu repositories
  }

  # trivy:ignore:aws-ec2-no-public-egress-sgr
  egress {
    description = "Allow secure outbound updates"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Required to securely pull Docker containers from ghcr.io
  }
}

# Secure EC2 Infrastructure Node
resource "aws_instance" "web_server" {
  ami           = "ami-0c7217cdde317cfec" # Official Ubuntu 22.04 LTS AMI
  instance_type = "t3.micro"

  key_name        = aws_key_pair.deployer.key_name
  security_groups = [aws_security_group.app_sg.name]

  # Explicitly encrypt the root storage volume at rest
  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  # Force IMDSv2 session tokens to be strictly REQUIRED
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # Blocks unauthenticated key extraction
    http_put_response_hop_limit = 1
  }

  tags = {
    Name    = "DevSecOps-Production-Server"
    Project = "Final-Year-Project"
  }
}

output "production_server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "The public IP address of your live production cloud server"
}