# ⚠️  TEST FILE — deliberately insecure, for PR review agent demo
#
# RDS database security group with overly permissive ingress rules.
# Intentional misconfiguration to demonstrate SecurityAgent detection.

resource "aws_security_group" "rds_public" {
  name        = "rds-public-access"
  description = "RDS database accessible from the internet"
  vpc_id      = var.vpc_id

  # INSECURE: MySQL/Aurora open to entire internet
  ingress {
    description = "MySQL from anywhere"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: PostgreSQL open to entire internet
  ingress {
    description = "PostgreSQL from anywhere"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: MS SQL open to entire internet
  ingress {
    description = "MSSQL from anywhere"
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: unrestricted egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "rds-public-access"
    Environment = "demo"
  }
}

resource "aws_db_instance" "demo" {
  identifier        = "demo-db"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "appdb"
  username = "admin"
  password = "changeme123"   # INSECURE: hardcoded password

  # INSECURE: database exposed to public internet
  publicly_accessible    = true
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds_public.id]
}
