CREATE TABLE IF NOT EXISTS core.data_sources (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 business_id UUID NOT NULL REFERENCES core.businesses(id),
 name TEXT NOT NULL CHECK (length(trim(name)) > 0),
 source_type TEXT NOT NULL CHECK (source_type IN ('api','csv','excel','shopify','woocommerce','sql','pos','manual')),
 status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
 last_successful_sync_at TIMESTAMPTZ,
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (business_id,name), CONSTRAINT data_sources_business_id_id_key UNIQUE (business_id,id)
);
CREATE INDEX IF NOT EXISTS data_sources_business_id_idx ON core.data_sources(business_id);
