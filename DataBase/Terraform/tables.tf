resource "terraform_data" "businesses" {
  depends_on = [terraform_data.schema]
  triggers_replace = [local.target, local.script_hash, filesha256("${path.module}/sql/businesses.sql")]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash scripts/apply.sh businesses"
    environment = local.connection
  }
}

resource "terraform_data" "data_sources" {
  depends_on = [terraform_data.businesses]
  triggers_replace = [local.target, local.script_hash, filesha256("${path.module}/sql/data_sources.sql")]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash scripts/apply.sh data_sources"
    environment = local.connection
  }
}

resource "terraform_data" "products" {
  depends_on = [terraform_data.businesses]
  triggers_replace = [local.target, local.script_hash, filesha256("${path.module}/sql/products.sql")]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash scripts/apply.sh products"
    environment = local.connection
  }
}

resource "terraform_data" "offers" {
  depends_on = [terraform_data.products, terraform_data.data_sources]
  triggers_replace = [local.target, local.script_hash, filesha256("${path.module}/sql/offers.sql")]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash scripts/apply.sh offers"
    environment = local.connection
  }
}
