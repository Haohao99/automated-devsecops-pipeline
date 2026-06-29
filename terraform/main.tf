# =======================================================================
# ☁️ DEVSECOPS TERRAFORM CONFIGURATION WITH EC2 + RDS MYSQL + PROMETHEUS + GRAFANA
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

variable "db_username" {
  type    = string
  default = "admin"
}

variable "db_password" {
  type      = string
  sensitive = true
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "fyp-deploy-key"
  public_key = file("../fyp_deploy_key.pub")
}

resource "aws_security_group" "app_sg" {
  name        = "employee-portal-security-group-secure"
  description = "Allow inbound SSH, Flask, Prometheus, and Grafana traffic"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name    = "DevSecOps-App-Security-Group"
    Project = "Final-Year-Project"
  }
}

# trivy:ignore:AWS-0107
resource "aws_security_group_rule" "app_ssh_ingress" {
  type              = "ingress"
  description       = "Allow SSH for GitHub Actions deployment"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}

resource "aws_security_group_rule" "app_flask_ingress" {
  type              = "ingress"
  description       = "Allow Flask web traffic"
  from_port         = 5000
  to_port           = 5000
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}

resource "aws_security_group_rule" "app_prometheus_ingress" {
  type              = "ingress"
  description       = "Allow Prometheus access"
  from_port         = 9090
  to_port           = 9090
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}

resource "aws_security_group_rule" "app_grafana_ingress" {
  type              = "ingress"
  description       = "Allow Grafana access"
  from_port         = 3000
  to_port           = 3000
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}

# trivy:ignore:AWS-0104
resource "aws_security_group_rule" "app_http_egress" {
  type              = "egress"
  description       = "Allow HTTP outbound for package updates"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}

# trivy:ignore:AWS-0104
resource "aws_security_group_rule" "app_https_egress" {
  type              = "egress"
  description       = "Allow HTTPS outbound for Docker, GitHub and updates"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app_sg.id
}

resource "aws_security_group" "rds_sg" {
  name        = "campus-ledger-rds-sg"
  description = "Allow MySQL access from EC2 only"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name    = "Campus-Ledger-RDS-Security-Group"
    Project = "Final-Year-Project"
  }
}

resource "aws_security_group_rule" "rds_mysql_ingress" {
  type                     = "ingress"
  description              = "Allow MySQL from Flask EC2 only"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app_sg.id
  security_group_id        = aws_security_group.rds_sg.id
}

resource "aws_security_group_rule" "app_mysql_egress" {
  type                     = "egress"
  description              = "Allow MySQL outbound to RDS"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rds_sg.id
  security_group_id        = aws_security_group.app_sg.id
}

resource "aws_db_subnet_group" "campus_db_subnet_group" {
  name       = "campus-ledger-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name    = "Campus Ledger DB Subnet Group"
    Project = "Final-Year-Project"
  }
}

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

  publicly_accessible        = false
  backup_retention_period    = 7
  skip_final_snapshot        = true
  deletion_protection        = false
  auto_minor_version_upgrade = true

  tags = {
    Name    = "Campus Ledger RDS MySQL"
    Project = "Final-Year-Project"
  }
}

resource "aws_instance" "web_server" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t3.micro"

  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  # This makes Terraform recreate the EC2 instance when user_data changes.
  # user_data normally runs only when the EC2 instance is first created.
  user_data_replace_on_change = true

  user_data = <<-USERDATA
    #!/bin/bash
    set -e

    # Update packages
    apt-get update -y

    # Install Docker
    apt-get install -y docker.io

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    # Allow ubuntu user to run Docker without sudo after re-login
    usermod -aG docker ubuntu

    # Create Docker network for monitoring containers
    docker network create monitoring || true

    # Create folders
    mkdir -p /opt/prometheus
    mkdir -p /opt/grafana/provisioning/datasources

    # Create Prometheus configuration
    # host.docker.internal allows Prometheus container to scrape the Flask app running on EC2 port 5000.
    cat > /opt/prometheus/prometheus.yml <<'PROMCFG'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "employee-portal"
    metrics_path: /metrics
    static_configs:
      - targets: ["host.docker.internal:5000"]
PROMCFG

    # Create Grafana datasource configuration
    # This automatically adds Prometheus inside Grafana.
    cat > /opt/grafana/provisioning/datasources/prometheus.yml <<'GRAFANA_DS'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
GRAFANA_DS

    # Create persistent volumes
    docker volume create grafana-storage
    docker volume create prometheus-storage

    # Remove old containers if they exist
    docker rm -f prometheus || true
    docker rm -f grafana || true

    # Start Prometheus
    docker run -d \
      --name prometheus \
      --network monitoring \
      --add-host=host.docker.internal:host-gateway \
      -p 9090:9090 \
      --restart unless-stopped \
      -v /opt/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
      -v prometheus-storage:/prometheus \
      prom/prometheus

    # Start Grafana
    docker run -d \
      --name grafana \
      --network monitoring \
      -p 3000:3000 \
      --restart unless-stopped \
      -v grafana-storage:/var/lib/grafana \
      -v /opt/grafana/provisioning/datasources/prometheus.yml:/etc/grafana/provisioning/datasources/prometheus.yml \
      grafana/grafana
  USERDATA

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

output "prometheus_url" {
  value       = "http://${aws_instance.web_server.public_ip}:9090"
  description = "Direct browser link to Prometheus"
}

output "rds_endpoint" {
  value       = aws_db_instance.campus_ledger_db.address
  description = "RDS MySQL endpoint for Flask application"
}

output "rds_database_name" {
  value       = aws_db_instance.campus_ledger_db.db_name
  description = "RDS database name"
}