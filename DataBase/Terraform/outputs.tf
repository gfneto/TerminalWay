output "database" { value = var.database_name }
output "schema" { value = "core" }
output "tables" {
  value = ["core.businesses", "core.data_sources", "core.products", "core.offers"]
}
