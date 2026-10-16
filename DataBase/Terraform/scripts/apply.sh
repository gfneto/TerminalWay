#!/usr/bin/env bash
set -euo pipefail
# Do not use set -x: tokens must not be logged.
cd "$(dirname "$0")/.."
command -v aws >/dev/null
command -v psql >/dev/null
: "${PGHOST:?}" "${PGPORT:?}" "${PGUSER:?}" "${AWS_REGION:?}" "${TARGET_DB:?}"
# Includes regional RDS CAs and Amazon Root CA 1 used by this endpoint.
export PGSSLROOTCERT="${PGSSLROOTCERT:-$PWD/certs/${AWS_REGION}-combined-bundle.pem}"
[[ -r "$PGSSLROOTCERT" ]] || { echo "RDS CA bundle not found or not readable: $PGSSLROOTCERT" >&2; exit 1; }
[[ "$TARGET_DB" =~ ^[a-z][a-z0-9_]{0,62}$ ]] || { echo "Invalid database name" >&2; exit 1; }
export PGSSLMODE=verify-full PGCONNECT_TIMEOUT=90
export PGPASSWORD="$(aws rds generate-db-auth-token --hostname "$PGHOST" --port "$PGPORT" --username "$PGUSER" --region "$AWS_REGION")"
trap 'unset PGPASSWORD' EXIT
case "${1:-}" in
  database)
    export PGDATABASE=postgres
    psql -X -v ON_ERROR_STOP=1 -v target_db="$TARGET_DB" -f sql/000_database.sql
    ;;
  schema)
    export PGDATABASE="$TARGET_DB"
    psql -X -v ON_ERROR_STOP=1 --single-transaction -f sql/001_schema.sql
    ;;
  businesses|data_sources|products|offers|reader)
    export PGDATABASE="$TARGET_DB"
    psql -X -v ON_ERROR_STOP=1 -v target_db="$TARGET_DB" --single-transaction -f "sql/$1.sql"
    ;;
  *) echo "Usage: apply.sh database|schema|businesses|data_sources|products|offers|reader" >&2; exit 1 ;;
esac