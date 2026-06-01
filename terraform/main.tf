# =======================================================================
# ☁️ TERRAFORM CONFIGURATION FOR DEVSECOPS FYP HOSTING (CLEAN SINGLE PASS)
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
  region = "us-east-1" 
}

# 1. Upload your public key padlock to AWS
resource "aws_key_pair" "deployer" {
  key_name   = "fyp-deploy-key"
  public_key = file("../fyp_deploy_key.pub") # Reads your local generated public key
}

# 2. Create the Security Group (Firewall)
resource "aws_security_group" "app_sg" {
  name        = "employee-portal-security-group"
  description = "Allow inbound SSH, HTTP, and Flask traffic"

  # Allow Port 22 (SSH) for deployment control automation
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

  # Allow all outbound traffic so your server can update itself
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. Provision the AWS EC2 Instance (Virtual Cloud Server)
resource "aws_instance" "web_server" {
  ami           = "ami-0c7217cdde317cfec" # Official Ubuntu 22.04 LTS AMI (us-east-1)
  instance_type = "t3.micro"             # Free Tier Eligible instance size

  # Attach your authentication key pair and your firewall group to this machine
  key_name        = aws_key_pair.deployer.key_name
  security_groups = [aws_security_group.app_sg.name]

  tags = {
    Name    = "DevSecOps-Production-Server"
    Project = "Final-Year-Project"
  }
}

# 4. Output the public IP address so you can access the website later
output "production_server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "The public IP address of your live production cloud server"
}