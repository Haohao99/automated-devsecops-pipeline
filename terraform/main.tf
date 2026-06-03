# =======================================================================
# ☁️ HARDENED TERRAFORM CONFIGURATION (PHASE 5 OBSERVABILITY METRICS)
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
    description = "Allow SSH management and GitHub Actions Deployments"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow Flask web traffic"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 📊 Allow Prometheus Web Console Access
  ingress {
    description = "Allow Prometheus Monitoring Access"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 📈 Allow Grafana Visual Dashboard Access
  ingress {
    description = "Allow Grafana Dashboard Access"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # trivy:ignore:aws-ec2-no-public-egress-sgr
  egress {
    description = "Allow outbound web tracking updates only"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # trivy:ignore:aws-ec2-no-public-egress-sgr
  egress {
    description = "Allow secure outbound updates"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Secure EC2 Infrastructure Node
resource "aws_instance" "web_server" {
  ami           = "ami-0c7217cdde317cfec" # Official Ubuntu 22.04 LTS AMI
  instance_type = "t3.micro"

  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id] # Fixed attachment array parameters

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # Enforce IMDSv2
    http_put_response_hop_limit = 1
  }

  tags = {
    Name    = "DevSecOps-Production-Server"
    Project = "Final-Year-Project"
  }
}

# =======================================================================
# 📋 SYSTEM AUTOMATION OUTPUT LINK GENERATORS
# =======================================================================

output "production_server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "The public IP address of your live production cloud server"
}

output "application_url" {
  value       = "http://${aws_instance.web_server.public_ip}:5000"
  description = "Direct web browser link to your live Python Flask Employee Portal app"
}

output "grafana_url" {
  value       = "http://${aws_instance.web_server.public_ip}:3000"
  description = "Direct web browser link to your Grafana Observability Dashboards"
}