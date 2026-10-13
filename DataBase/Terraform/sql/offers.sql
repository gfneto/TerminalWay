CREATE TABLE IF NOT EXISTS core.offers (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 business_id UUID NOT NULL REFERENCES core.businesses(id),
 product_id UUID NOT NULL, source_id UUID NOT NULL,
 external_id TEXT NOT NULL CHECK (length(trim(external_id)) > 0),
 price NUMERIC(18,4) NOT NULL CHECK (price >= 0),
 currency VARCHAR(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
 stock_quantity NUMERIC(18,3) CHECK (stock_quantity >= 0),
 availability TEXT NOT NULL DEFAULT 'unknown' CHECK (availability IN ('in_stock','out_of_stock','preorder','unknown')),
 source_updated_at TIMESTAMPTZ, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(), expires_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY (business_id,product_id) REFERENCES core.products(business_id,id),
 FOREIGN KEY (business_id,source_id) REFERENCES core.data_sources(business_id,id),
 UNIQUE (business_id,source_id,external_id)
);
CREATE INDEX IF NOT EXISTS offers_business_product_idx ON core.offers(business_id,product_id);
CREATE INDEX IF NOT EXISTS offers_business_source_idx ON core.offers(business_id,source_id);
