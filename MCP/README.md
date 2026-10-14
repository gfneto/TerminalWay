# TerminalWay MCP server

Python MCP server exposing two read-only tools: `search_products` and `get_offer`. Includes catalogue functions, an Aurora IAM/TLS connection, stdio and authenticated Streamable HTTP transports, a Dockerfile, and a protocol test client. The server and smoke client are kept together in this project for local testing.

This is a runnable server project, not an AWS deployment. No remote service, IAM role or SQL role has been created by this delivery.

## Setup

Python 3.10+ and an AWS identity authorized for the chosen PostgreSQL user are required. The Python requirements include Botocore's CRT extra so boto3 can load credentials from the AWS CLI `aws login` provider.

```bash
cd terminalway-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
curl --fail --location https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o "$HOME/global-bundle.pem"
cp .env.example .env
# Edit .env: set the CA path and actual authorized business UUIDs.
source .env
```

Find business IDs in psql with `SELECT id, name FROM core.businesses;`. The allowlist is controlled by the server, not exposed as a tool parameter. All authenticated HTTP callers share that allowlist.

Run [reader.sql](./reader.sql) as a PostgreSQL administrator connected to the `terminalway` database. It creates the dedicated reader role if needed and grants read access to the catalogue tables. The AWS caller also needs `rds-db:connect` for `terminalway_reader`.

IAM resource format: `arn:aws:rds-db:eu-north-1:ACCOUNT_ID:dbuser:CLUSTER_RESOURCE_ID/terminalway_reader`. Obtain the cluster resource ID with `describe-db-clusters`. Never commit access keys or tokens. AWS authentication comes from the standard credential chain, including local CLI login or workload roles.

## Local stdio test

```bash
python client_test.py
python client_test.py --query Cement --currency GBP --max-price 10
python client_test.py --offer-id ACTUAL_OFFER_UUID
```

The client launches the server subprocess, lists tools, calls one tool and prints its MCP response. Omit `--query` to list offers without a text filter; the client fetches up to 100 per page by default. If `has_more` is true, pass `next_offset` with `--offset` for the next page. Results are offers, not deduplicated products.

## HTTP test

Configure `MCP_API_TOKENS` on the server as a JSON object mapping each client name to a distinct random token of at least 32 ASCII characters. Store the token map in a secret manager in deployment, and give each client only its own key in `MCP_API_TOKEN`. Removing a client's entry and restarting the server revokes that key. For a local one-key test, the legacy `MCP_API_TOKEN` setting is also supported.

Run the server:

```bash
python -m terminalway.mcp_server --transport http
```

From another shell, set that client's key and run:

```bash
python client_test.py --url http://127.0.0.1:8000/mcp
```

Use HTTPS for remote HTTP connections. Unauthenticated requests receive 401. `/health` is an unauthenticated liveness endpoint and does not query the database. Bearer keys are not a full MCP OAuth implementation; all keys share the same business allowlist and do not provide per-business scopes or rate limits.

## Container deployment

Build with `docker build -t terminalway-mcp .`. Run on ECS/Fargate or another ASGI-capable container service behind HTTPS with:

- An AWS task role with narrowly scoped `rds-db:connect`.
- The CA bundle mounted at `RDS_CA_BUNDLE` and the database environment values.
- `MCP_API_TOKENS` injected from Secrets Manager.
- `MCP_ALLOWED_HOSTS` set to the forwarded host and `MCP_ALLOWED_ORIGINS` set to permitted browser origins.
- `/health` for load-balancer liveness; separately verify database readiness.

The Dockerfile uses a non-root user and does not bake credentials or certificates into the image. Do not expose unencrypted HTTP remotely.

## Tool semantics

`search_products` matches all whitespace-separated terms using parameterized ILIKE across product name, brand and description when a query is supplied; omit the query to list active offers without a text filter. Filters include currency, maximum price (requires currency), availability, limit and offset. Explicitly expired offers and inactive entities are excluded.

`get_offer` accepts an offer UUID. Missing, inactive and unauthorized offers return `found: false`; expired offers remain readable and are labelled. Both tools read stored merchant data, not live stock, and do not reserve products, accept payment or create orders.

## Validation

```bash
python -m unittest discover -s tests -v
```

Tests cover catalogue validation and protocol calls using a fake database, including HTTP authentication. Live Aurora connectivity must be verified in the configured AWS environment.
