CREATE TABLE IF NOT EXISTS core.products (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 business_id UUID NOT NULL REFERENCES core.businesses(id),
 sku TEXT NOT NULL CHECK (length(trim(sku)) > 0),
 name TEXT NOT NULL CHECK (length(trim(name)) > 0),
 description TEXT, brand TEXT, gtin TEXT, category TEXT,
 status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (business_id,sku), CONSTRAINT products_business_id_id_key UNIQUE (business_id,id)
);
