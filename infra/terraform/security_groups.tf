# ⚠️  TEST FILE — deliberately insecure, for PR review agent validation
#
# This security group is intentionally misconfigured to test whether
# the AI-DLC SecurityAgent correctly flags overly permissive rules.

resource "aws_security_group" "web_open" {
  name        = "web-open-to-world"
  description = "Allow all inbound traffic (INSECURE)"
  vpc_id      = var.vpc_id

  # INSECURE: opens ALL ports to the entire internet
  ingress {
    description = "Allow everything from anywhere"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: SSH wide open to internet
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: RDP wide open to internet
  ingress {
    description = "RDP from anywhere"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # INSECURE: unrestricted egress (common but worth flagging)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "web-open-to-world"
    Environment = "test"
  }
}

variable "vpc_id" {
  description = "VPC to place the security group in"
  type        = string
  default     = "vpc-00000000"
}
