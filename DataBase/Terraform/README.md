# TerminalWay PostgreSQL schema deployment with Terraform

This project creates the PostgreSQL database `terminalway`, schema `core` and four tables on the EXISTING Aurora cluster. It does not provision Aurora infrastructure, networking or AWS permissions. Use the separate Aurora adoption project for cluster management.

## Layout

- postgres.tf: creates the internal database if missing.
- schema.tf: creates the core schema if missing.
- tables.tf: applies each table's SQL in dependency order.
- variables.tf, locals.tf, versions.tf, outputs.tf: configuration.
- sql/: table DDL, keys, checks and indexes matching our existing design.
- scripts/apply.sh: fresh IAM token per operation, verified TLS and fail-fast SQL execution.

Terraform orchestrates SQL through built-in terraform_data/local-exec. These are execution markers, not native PostgreSQL table resources. No third-party provider or AWS secret is stored in state. AWS authentication is inherited from the machine running Terraform.

## Run in AWS CloudShell

Requirements: Terraform >=1.5, AWS CLI, psql and permission to connect as postgres. Commands run from the shell prompt, NOT inside psql.

```bash
curl --fail --location https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o "$HOME/global-bundle.pem"
cd terminalway-db-terraform
cp examples.tfvars terraform.tfvars
terraform init
terraform fmt
terraform validate
terraform plan -out=database.tfplan
terraform apply database.tfplan
```

Verify the certificate path in terraform.tfvars. On macOS, also authenticate AWS CLI for the correct project and install Terraform and psql. CloudShell already had working AWS authentication and psql in our session; Terraform availability must be checked separately.

## Existing tables and data

The database, schema, tables and indexes use existence checks. Applying against our already-created objects does not delete them or insert duplicate demo data. Existing structures are NOT reconciled: IF NOT EXISTS only skips existing tables, it does not validate or repair differences. Compare existing DDL with the SQL files before adopting another database. This package intentionally omits sample data.

Changing a SQL file changes its hash and reruns the corresponding execution marker. Editing CREATE TABLE definitions will NOT alter an existing table. Use explicit, versioned ALTER TABLE migrations for future schema changes. This is a bootstrap implementation, not a general schema migration engine.

terraform plan does not inspect PostgreSQL object drift. If a table is manually dropped, a no-change plan will not recreate it unless that operation is rerun. Example:

```bash
terraform apply -replace=terraform_data.products
```

Replacements of these markers do not delete SQL objects. terraform destroy removes the markers from Terraform state; it does NOT drop databases, schemas, tables or records. There are no destroy provisioners.

Each table operation is transactional. The entire deployment is not a single transaction because CREATE DATABASE cannot run inside one. Failure stops the deployment; successful earlier stages remain and retries are safe with matching existing DDL. Run one deployment at a time, keep the state and lock it when collaborating.

## Verify in psql

```psql
\connect terminalway
\dt core.*
\d core.offers
```

Expected tables: businesses, data_sources, products, offers. Composite foreign keys prevent cross-business product/source references in offers. updated_at is not automatically refreshed on updates, matching the current database.

## Validation status

Shell syntax was checked in the authoring environment. Terraform and AWS credentials were not available there, so init/validate/plan and execution against Aurora were not run. No live database changes were made by the authoring session. Review and run the commands above in your authenticated environment.
