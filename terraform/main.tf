# =======================================================================
# ☁️ TERRAFORM CONFIGURATION FOR DEVSECOPS FYP HOSTING
# =======================================================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider Region
provider "aws" {
  region = "us-east-1" # Industry standard region for free tier availability
}

# 1. Create a Secure Security Group (Virtual Firewall)
resource "aws_security_group" "app_sg" {
  name        = "employee-portal-security-group"
  description = "Allow inbound SSH, HTTP, and Flask traffic"

  # Allow Port 22 (SSH) so your upcoming pipeline can deploy code securely
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow Port 5000 (Your Flask Web Application Port)
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic so your server can download updates/Docker images
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. Provision an AWS EC2 Instance (Virtual Cloud Server)
resource "aws_instance" "web_server" {
  ami           = "ami-0c7217cdde317cfec" # Official Ubuntu 22.04 LTS AMI (us-east-1)
  instance_type = "t2.micro"             # 100% Free Tier Eligible instance size

  security_groups = [aws_security_group.app_sg.name]

  tags = {
    Name = "DevSecOps-Production-Server"
    Project = "Final-Year-Project"
  }
}

# 3. Output the public IP address so you can access the website later
output "production_server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "The public IP address of your live production cloud server"
}
