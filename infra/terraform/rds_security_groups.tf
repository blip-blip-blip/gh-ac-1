ingress {
  description = "MySQL from trusted network"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"
  cidr_blocks = ["<trusted-CIDR-block>"]
}