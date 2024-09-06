# child applications
resource "azuread_application" "child_app" {
  count        = 2
  display_name = "child_app_${count.index}"
  owners       = [azuread_service_principal.github_sp.object_id]
}