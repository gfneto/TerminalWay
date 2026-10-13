variable "aws_region" {
  type    = string
  default = "eu-north-1"
}
variable "host" {
  type    = string
  default = "terminalway-dev01.cluster-cd2gwcuy4tcm.eu-north-1.rds.amazonaws.com"
}
variable "port" {
  type    = number
  default = 5432
}
variable "database_name" {
  type    = string
  default = "terminalway"
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,62}$", var.database_name))
    error_message = "Use a lowercase PostgreSQL identifier of up to 63 characters."
  }
}
variable "username" {
  type    = string
  default = "postgres"
}
variable "ssl_root_cert" {
  type        = string
  description = "Absolute path to the downloaded official RDS CA bundle."
}
