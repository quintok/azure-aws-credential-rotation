###
### These are the resources that will allow github to access Entra resources.
###

data "azuread_application_published_app_ids" "well_known" {}

resource "azuread_service_principal" "msgraph" {
  client_id    = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]
  use_existing = true
}

# Define the Azure AD application
resource "azuread_application" "github_oidc" {
  display_name = "github-oidc-app"

  required_resource_access {
    resource_app_id = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]

    resource_access {
      id   = azuread_service_principal.msgraph.app_role_ids["Application.ReadWrite.OwnedBy"]
      type = "Role"
    }
  }
}

resource "azuread_service_principal_delegated_permission_grant" "example" {
  service_principal_object_id          = azuread_service_principal.github_sp.object_id
  resource_service_principal_object_id = azuread_service_principal.msgraph.object_id
  claim_values                         = ["Application.ReadWrite.OwnedBy"]
}

resource "azuread_service_principal" "github_sp" {
  client_id                    = azuread_application.github_oidc.client_id
  app_role_assignment_required = false
}

# Define the OIDC settings for the GitHub repository
resource "azuread_application_federated_identity_credential" "github_oidc_credential" {
  application_id = azuread_application.github_oidc.id
  display_name   = "GitHubOIDC"
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = var.github_oidc_subject
  audiences      = ["api://AzureADTokenExchange"]
}