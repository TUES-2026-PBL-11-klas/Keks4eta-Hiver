variable "cidr_block" {}
variable "environment" {}

resource "aws_vpc" "hiver" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  tags = { Name = "hiver-${var.environment}" }
}

output "vpc_id" {
  value = aws_vpc.hiver.id
}

output "private_subnet_ids" {
  value = []
}
