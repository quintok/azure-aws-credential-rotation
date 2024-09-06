terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "2.53.1"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "5.65.0"
    }

  }
}

provider "aws" {
}

provider "azuread" {
}