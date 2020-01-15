provider "azurerm" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=1.38.0"
}
resource "azurerm_resource_group" "rg" {
  name     = "CROP_test"
  location = "UK South"
}
