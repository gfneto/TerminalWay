-- Run as postgres while connected to the configured target database.
-- Adds a dedicated IAM-authenticated read-only role.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'terminalway_reader') THEN
        CREATE ROLE terminalway_reader LOGIN;
    END IF;
END $$;
GRANT rds_iam TO terminalway_reader;
GRANT CONNECT ON DATABASE :"target_db" TO terminalway_reader;
GRANT USAGE ON SCHEMA core TO terminalway_reader;
GRANT SELECT ON core.businesses, core.products, core.data_sources, core.offers TO terminalway_reader;
-- Also grant the calling AWS identity rds-db:connect for this database user.
-- Discover the cluster resource ID (not its human-readable identifier) first.
