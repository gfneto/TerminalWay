CREATE TABLE IF NOT EXISTS core.businesses (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 name TEXT NOT NULL CHECK (length(trim(name)) > 0),
 legal_name TEXT, website TEXT,
 country_code VARCHAR(2) CHECK (country_code ~ '^[A-Z]{2}$'),
 status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
