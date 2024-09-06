variable "github_oidc_subject" {
  description = "The oidc subject used to constrain access from Entra and AWS.  See https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect#example-subject-claims"
  type        = string
  default     = "repo:quintok/azure-aws-credential-rotation:ref:refs/heads/main"
}

variable "aws_oidc_name" {
  type    = string
  default = "github-oidc-provider"
}

variable "aws_oidc_url" {
  type    = string
  default = "https://token.actions.githubusercontent.com"
}

variable "aws_oidc_audience" {
  type    = string
  default = "sts.amazonaws.com"
}

variable "github_cert_thumbprint" {
  description = "The thumbprint of the GitHub certificate used to sign the OIDC tokens.  Follow https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html to get the thumbprint"
  type        = string
  default     = "d89e3bd43d5d909b47a18977aa9d5ce36cee184c"
}