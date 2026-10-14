"""Aurora IAM connection: one fresh token and read-only connection per operation."""
import os
from pathlib import Path


class Database:
    def __init__(self):
        self.host = os.environ['RDS_HOST']
        self.region = os.environ.get('AWS_REGION', 'eu-north-1')
        self.port = int(os.environ.get('RDS_PORT', '5432'))
        self.name = os.environ.get('RDS_DATABASE', 'terminalway')
        self.user = os.environ.get('RDS_USER', 'terminalway_reader')
        self.ca = os.environ['RDS_CA_BUNDLE']
        if not Path(self.ca).is_file():
            raise ValueError('RDS_CA_BUNDLE must point to an existing CA bundle')

    def fetch(self, sql, params):
        import boto3
        import psycopg
        from psycopg.rows import dict_row
        token = boto3.client('rds', region_name=self.region).generate_db_auth_token(
            DBHostname=self.host, Port=self.port, DBUsername=self.user, Region=self.region)
        with psycopg.connect(host=self.host, port=self.port, dbname=self.name,
                             user=self.user, password=token, sslmode='verify-full',
                             sslrootcert=self.ca, connect_timeout=90,
                             options='-c default_transaction_read_only=on -c statement_timeout=10000',
                             row_factory=dict_row) as conn:
            return conn.execute(sql, params).fetchall()
