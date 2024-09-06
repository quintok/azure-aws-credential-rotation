
resource "aws_iam_openid_connect_provider" "github_oidc_provider" {
  url             = var.aws_oidc_url
  client_id_list  = [var.aws_oidc_audience]
  thumbprint_list = [var.github_cert_thumbprint]
}

resource "aws_iam_role" "github_oidc_role" {
  name = "github-oidc-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          "Federated" : aws_iam_openid_connect_provider.github_oidc_provider.arn
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = var.aws_oidc_audience
            "token.actions.githubusercontent.com:sub" = var.github_oidc_subject
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secretmanager" {
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
  role       = aws_iam_role.github_oidc_role.name
}