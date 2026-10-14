#!/usr/bin/env bash
set -euo pipefail
# Do not use set -x: the temporary IAM token must not be logged.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

readonly DATABASE_NAME="terminalway"
export PGHOST="terminalway-dev01.cluster-cd2gwcuy4tcm.eu-north-1.rds.amazonaws.com"
export PGPORT="5432"
export PGUSER="postgres"
export AWS_REGION="eu-north-1"
export PGDATABASE="postgres"
export PGSSLROOTCERT="$TERRAFORM_DIR/certs/eu-north-1-combined-bundle.pem"
export PGSSLMODE="verify-full"
export PGCONNECT_TIMEOUT="90"

printf 'WARNING: this permanently deletes the "%s" database and all its data.\n' "$DATABASE_NAME" >&2
read -r -p "Type 'DROP ${DATABASE_NAME}' to continue: " confirmation
if [[ "$confirmation" != "DROP $DATABASE_NAME" ]]; then
    echo "Confirmation did not match; no database changes were made." >&2
    exit 1
fi

command -v aws >/dev/null || { echo "AWS CLI is required." >&2; exit 1; }
command -v psql >/dev/null || { echo "psql is required." >&2; exit 1; }
[[ -r "$PGSSLROOTCERT" ]] || {
    echo "RDS CA bundle not found or not readable: $PGSSLROOTCERT" >&2
    exit 1
}

export PGPASSWORD
PGPASSWORD="$(aws rds generate-db-auth-token \
    --hostname "$PGHOST" \
    --port "$PGPORT" \
    --username "$PGUSER" \
    --region "$AWS_REGION")"
trap 'unset PGPASSWORD' EXIT

psql -X -v ON_ERROR_STOP=1 \
    --command="DROP DATABASE ${DATABASE_NAME} WITH (FORCE);"
