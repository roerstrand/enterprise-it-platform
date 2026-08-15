terraform {
    required_providers {
        azurerm = {
            source = "hashicorp/azurerm"
            version = "~> 4.0" 
        }
        azuread = {
            source = "hashicorp/azuread"
            version = "~> 3.0"
        }
    }
}

provider "azurerm" {
    features {}
}

provider "azuread" {}

resource "azurerm_resource_group" "main" {
 name = "enterprise-it-platform-rg"
 location = "swedencentral"
}

resource "azurerm_container_registry" "main" {
    name = "enterpriseitplatformacr"
    resource_group_name = azurerm_resource_group.main.name
    location = azurerm_resource_group.main.location
    sku = "Basic"
}

resource "azuread_application" "github_actions" {
    display_name = "enterprise-it-platform-github-actions"
}

resource "azuread_service_principal" "github_actions" {
    client_id = azuread_application.github_actions.client_id
}

resource "azuread_application_federated_identity_credential" "github_actions_main" {
    application_id = azuread_application.github_actions.id
    display_name = "github-actions-main-branch"
    audiences = ["api://AzureADTokenExchange"]
    issuer = "https://token.actions.githubusercontent.com"
    subject = "repo:roerstrand/enterprise-it-platform:ref:refs/heads/main"
}

resource "azurerm_role_assignment" "github_actions_acr_push" {
    scope = azurerm_container_registry.main.id
    role_definition_name = "AcrPush"
    principal_id = azuread_service_principal.github_actions.object_id
}

data "azurerm_client_config" "current" {}

output "github_actions_client_id" {
    value = azuread_application.github_actions.client_id
}

output "azure_tenant_id" {
    value = data.azurerm_client_config.current.tenant_id
}

output "azure_subscription_id" {
    value = data.azurerm_client_config.current.subscription_id
}
