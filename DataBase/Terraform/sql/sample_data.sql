BEGIN;

CREATE TEMPORARY TABLE demo_businesses (
    business_no INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO demo_businesses (business_no, name, website) VALUES
    (1, 'Northstar Building Supplies', 'https://northstar.example.com'),
    (2, 'Atlas Construction Materials', 'https://atlas.example.com'),
    (3, 'Summit Builders Depot', 'https://summit.example.com'),
    (4, 'Riverside Construction Supply', 'https://riverside.example.com'),
    (5, 'Pioneer Building Products', 'https://pioneer.example.com'),
    (6, 'Cedar Valley Materials', 'https://cedarvalley.example.com'),
    (7, 'Keystone Builders Warehouse', 'https://keystone.example.com'),
    (8, 'Redwood Construction Supply', 'https://redwood.example.com'),
    (9, 'Blue Ridge Building Center', 'https://blueridge.example.com'),
    (10, 'Ironclad Building Materials', 'https://ironclad.example.com');

CREATE TEMPORARY TABLE demo_products (
    product_no INTEGER PRIMARY KEY,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    base_price NUMERIC(18, 4) NOT NULL
) ON COMMIT DROP;

INSERT INTO demo_products (
    product_no, sku, name, description, brand, category, base_price
) VALUES
    (
        1, 'CEM-50LB', 'Portland Cement, 50 lb Bag',
        'Type I/II Portland cement in a 50 lb bag.',
        'FoundationPro', 'Cement and Concrete', 9.49
    ),
    (
        2, 'CON-1CYD', 'Ready-Mix Concrete, 1 Cubic Yard',
        'Ready-mix concrete sold by the cubic yard.',
        'FoundationPro', 'Cement and Concrete', 145.00
    ),
    (
        3, 'REB-4-20', 'Reinforcing Steel Rebar, #4 x 20 ft',
        'Grade 60 reinforcing steel rebar, #4 bar, 20 ft length.',
        'IronPeak', 'Steel and Reinforcement', 12.75
    ),
    (
        4, 'LUM-PT-448', 'Pressure-Treated Lumber, 4 x 4 x 8 ft',
        'Pressure-treated dimensional lumber, nominal 4 x 4, 8 ft length.',
        'Timberline', 'Lumber', 13.99
    ),
    (
        5, 'BRK-CLAY-STD', 'Standard Clay Brick, Each',
        'Standard red clay brick sold individually.',
        'Brickworks', 'Masonry', 0.89
    ),
    (
        6, 'DRY-12-4X8', 'Gypsum Drywall Board, 1/2 in x 4 ft x 8 ft',
        'Standard 1/2 in gypsum drywall board, 4 ft by 8 ft.',
        'WallSure', 'Drywall and Insulation', 16.49
    ),
    (
        7, 'AGG-CRUSH-1CYD', 'Crushed Stone Aggregate, 1 Cubic Yard',
        'Crushed stone aggregate sold by the cubic yard.',
        'StonePath', 'Aggregates', 48.50
    );

INSERT INTO core.businesses (
    id, name, legal_name, website, country_code, status, metadata
)
SELECT
    ('11000000-0000-4000-8000-' || lpad(business_no::text, 12, '0'))::uuid,
    name,
    name || ', Inc.',
    website,
    'US',
    'active',
    '{"sample_data": true, "industry": "construction materials"}'::jsonb
FROM demo_businesses
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    legal_name = EXCLUDED.legal_name,
    website = EXCLUDED.website,
    country_code = EXCLUDED.country_code,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata,
    updated_at = now();

INSERT INTO core.data_sources (
    id, business_id, name, source_type, status,
    last_successful_sync_at, metadata
)
SELECT
    ('21000000-0000-4000-8000-' || lpad(business_no::text, 12, '0'))::uuid,
    ('11000000-0000-4000-8000-' || lpad(business_no::text, 12, '0'))::uuid,
    'Demo Product Catalog',
    'manual',
    'active',
    now() - interval '15 minutes',
    '{"sample_data": true}'::jsonb
FROM demo_businesses
ON CONFLICT (id) DO UPDATE SET
    business_id = EXCLUDED.business_id,
    name = EXCLUDED.name,
    source_type = EXCLUDED.source_type,
    status = EXCLUDED.status,
    last_successful_sync_at = EXCLUDED.last_successful_sync_at,
    metadata = EXCLUDED.metadata,
    updated_at = now();

INSERT INTO core.products (
    id, business_id, sku, name, description, brand, category, status, metadata
)
SELECT
    (
        '31000000-0000-4000-8000-' ||
        lpad(((business.business_no - 1) * 7 + product.product_no)::text, 12, '0')
    )::uuid,
    ('11000000-0000-4000-8000-' || lpad(business.business_no::text, 12, '0'))::uuid,
    product.sku,
    product.name,
    product.description,
    product.brand,
    product.category,
    'active',
    jsonb_build_object('sample_data', true, 'unit_price_currency', 'USD')
FROM demo_businesses AS business
CROSS JOIN demo_products AS product
ON CONFLICT (id) DO UPDATE SET
    business_id = EXCLUDED.business_id,
    sku = EXCLUDED.sku,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    brand = EXCLUDED.brand,
    category = EXCLUDED.category,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata,
    updated_at = now();

INSERT INTO core.offers (
    business_id, product_id, source_id, external_id, price, currency,
    stock_quantity, availability, source_updated_at, expires_at
)
SELECT
    ('11000000-0000-4000-8000-' || lpad(business.business_no::text, 12, '0'))::uuid,
    (
        '31000000-0000-4000-8000-' ||
        lpad(((business.business_no - 1) * 7 + product.product_no)::text, 12, '0')
    )::uuid,
    ('21000000-0000-4000-8000-' || lpad(business.business_no::text, 12, '0'))::uuid,
    'CAT-' || lpad(business.business_no::text, 2, '0')
        || '-' || lpad(product.product_no::text, 2, '0'),
    product.base_price + (business.business_no * 0.37),
    'USD',
    CASE (business.business_no + product.product_no) % 4
        WHEN 0 THEN 0
        WHEN 1 THEN NULL
        ELSE 10 + business.business_no + product.product_no
    END,
    CASE (business.business_no + product.product_no) % 4
        WHEN 0 THEN 'out_of_stock'
        WHEN 1 THEN 'unknown'
        WHEN 2 THEN 'in_stock'
        ELSE 'in_stock'
    END,
    now() - interval '15 minutes',
    now() + interval '24 hours'
FROM demo_businesses AS business
CROSS JOIN demo_products AS product
ON CONFLICT (business_id, source_id, external_id) DO UPDATE SET
    product_id = EXCLUDED.product_id,
    price = EXCLUDED.price,
    currency = EXCLUDED.currency,
    stock_quantity = EXCLUDED.stock_quantity,
    availability = EXCLUDED.availability,
    source_updated_at = EXCLUDED.source_updated_at,
    ingested_at = now(),
    expires_at = EXCLUDED.expires_at,
    updated_at = now();

COMMIT;
