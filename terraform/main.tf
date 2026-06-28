# =======================================================================
# ☁️ DEVSECOPS TERRAFORM CONFIGURATION WITH EC2 + RDS MYSQL
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

# =======================================================================
# 🔐 VARIABLES
# =======================================================================

variable "db_username" {
  type    = string
  default = "admin"
}

variable "db_password" {
  type      = string
  sensitive = true
}

# =======================================================================
# 🌐 DEFAULT VPC + SUBNETS
# =======================================================================

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# =======================================================================
# 🔑 EC2 KEY PAIR
# =======================================================================

resource "aws_key_pair" "deployer" {
  key_name   = "fyp-deploy-key"
  public_key = file("../fyp_deploy_key.pub")
}

# =======================================================================
# 🛡️ EC2 SECURITY GROUP
# =======================================================================

resource "aws_security_group" "app_sg" {
  name        = "employee-portal-security-group-secure"
  description = "Allow SSH, Flask, Prometheus, and Grafana traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow SSH management"
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

  ingress {
    description = "Allow Prometheus Monitoring Access"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow Grafana Dashboard Access"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow outbound traffic, including database connection to RDS"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "DevSecOps-App-Security-Group"
    Project = "Final-Year-Project"
  }
}

# =======================================================================
# 🗄️ RDS SECURITY GROUP
# =======================================================================

resource "aws_security_group" "rds_sg" {
  name        = "campus-ledger-rds-sg"
  description = "Allow MySQL access from EC2 Flask app only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Allow MySQL from EC2 app server only"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    description = "Allow outbound responses"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "Campus-Ledger-RDS-Security-Group"
    Project = "Final-Year-Project"
  }
}

# =======================================================================
# 🗄️ RDS SUBNET GROUP
# =======================================================================

resource "aws_db_subnet_group" "campus_db_subnet_group" {
  name       = "campus-ledger-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name    = "Campus Ledger DB Subnet Group"
    Project = "Final-Year-Project"
  }
}

# =======================================================================
# 🗄️ RDS MYSQL DATABASE
# =======================================================================

resource "aws_db_instance" "campus_ledger_db" {
  identifier = "campus-ledger-db"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"

  db_name  = "campus_ledger"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.campus_db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible      = false
  backup_retention_period  = 7
  skip_final_snapshot      = true
  deletion_protection      = false
  auto_minor_version_upgrade = true

  tags = {
    Name    = "Campus Ledger RDS MySQL"
    Project = "Final-Year-Project"
  }
}

# =======================================================================
# 💻 EC2 INSTANCE
# =======================================================================

resource "aws_instance" "web_server" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t3.micro"

  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name    = "DevSecOps-Production-Server"
    Project = "Final-Year-Project"
  }
}

# =======================================================================
# 📋 OUTPUTS
# =======================================================================

output "production_server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "The public IP address of the live production cloud server"
}

output "application_url" {
  value       = "http://${aws_instance.web_server.public_ip}:5000"
  description = "Direct browser link to Flask app"
}

output "grafana_url" {
  value       = "http://${aws_instance.web_server.public_ip}:3000"
  description = "Direct browser link to Grafana dashboard"
}

output "rds_endpoint" {
  value       = aws_db_instance.campus_ledger_db.address
  description = "RDS MySQL endpoint for Flask application"
}

output "rds_database_name" {
  value       = aws_db_instance.campus_ledger_db.db_name
  description = "RDS database name"
}