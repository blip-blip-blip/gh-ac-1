# ⚠️  TEST FILE — deliberately insecure, for PR review agent demo
#
# Application Load Balancer security group with overly permissive rules.
# Intentional misconfiguration to demonstrate SecurityAgent detection.

resource "aws_security_group" "alb_open" {
  name        = "alb-open-to-world"
  description = "ALB accepting all traffic"
  vpc_id      = var.vpc_id

  # INSECURE: all TCP ports open to entire internet
  ingress {
    description = "All TCP from anywhere"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: all UDP open to entire internet
  ingress {
    description = "All UDP from anywhere"
    from_port   = 0
    to_port     = 65535
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: ICMP unrestricted (allows ping flood)
  ingress {
    description = "All ICMP"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "alb-open-to-world"
    Environment = "demo"
  }
}

resource "aws_security_group" "app_servers" {
  name        = "app-servers"
  description = "App server security group"
  vpc_id      = var.vpc_id

  # INSECURE: app servers directly reachable from internet (should only allow ALB SG)
  ingress {
    description = "HTTP from anywhere"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: debug port open to internet
  ingress {
    description = "Remote debug port"
    from_port   = 5005
    to_port     = 5005
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
    Name        = "app-servers"
    Environment = "demo"
  }
}
