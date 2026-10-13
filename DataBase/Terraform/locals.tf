locals {
  connection = {
    PGHOST         = var.host
    PGPORT         = tostring(var.port)
    PGUSER         = var.username
    PGSSLROOTCERT  = var.ssl_root_cert
    AWS_REGION     = var.aws_region
    TARGET_DB      = var.database_name
  }
  target = [var.host, var.port, var.database_name, var.username, var.aws_region]
  script_hash = filesha256("${path.module}/scripts/apply.sh")
}
