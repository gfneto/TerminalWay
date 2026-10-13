resource "terraform_data" "schema" {
  depends_on       = [terraform_data.database]
  triggers_replace = [local.target, local.script_hash, filesha256("${path.module}/sql/001_schema.sql")]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash scripts/apply.sh schema"
    environment = local.connection
  }
}
