output "aws_role_arn" {
  description = "The ARN of the AWS role that can be assumed by the GitHub OIDC provider"
  value       = aws_iam_role.github_oidc_role.arn
}

output "azure_application_id" {
  description = "The Azure AD application ID for the GitHub OIDC application"
  value       = azuread_application.github_oidc.client_id
}