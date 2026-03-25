# Terraform Cloud configuration — configure org and workspace when ready
#
# terraform {
#   cloud {
#     organization = "<your-org>"
#     workspaces {
#       name = "<your-workspace>"
#     }
#   }
# }
#
# Example future resources:
#
# AWS OIDC provider for keyless GitHub Actions → AWS auth
# resource "aws_iam_openid_connect_provider" "github" { ... }
#
# DynamoDB table for trend data persistence (if needed beyond GitHub comments)
# resource "aws_dynamodb_table" "trend_data" { ... }
