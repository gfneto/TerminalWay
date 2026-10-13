# Uses the EXISTING Aurora endpoint. Does not create an RDS cluster.
resource "terraform_data" "database" {
  triggers_replace = [local.target, local.script_hash, filesha256("${path.module}/sql/000_database.sql")]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash scripts/apply.sh database"
    environment = local.connection
  }
}
