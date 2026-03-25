ingress {
  description = "Restrict access to specific ports and IP ranges"
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["<specific_cidr_block>"]
}