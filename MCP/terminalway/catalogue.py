"""Read-only catalogue operations, independent of MCP and the LLM."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID

SELECT = """
SELECT o.id AS offer_id, p.id AS product_id, b.id AS business_id,
       b.name AS business, p.sku, p.name AS product, p.description,
       p.brand, p.category, s.name AS source, o.price, o.currency,
       o.stock_quantity, o.availability, o.source_updated_at,
       o.ingested_at, o.expires_at,
       (o.expires_at IS NOT NULL AND o.expires_at <= now()) AS expired
FROM core.offers o
JOIN core.products p ON p.business_id = o.business_id AND p.id = o.product_id
JOIN core.businesses b ON b.id = o.business_id
JOIN core.data_sources s ON s.business_id = o.business_id AND s.id = o.source_id
WHERE b.status = 'active' AND p.status = 'active' AND s.status = 'active'
  AND o.business_id = ANY(%s::uuid[])
"""


def uuid_string(value):
    return str(UUID(str(value)))


def json_value(value):
    if isinstance(value, Decimal):
        return str(value)  # Exact monetary values; never convert to float.
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_value(v) for v in value]
    return value


class Catalogue:
    def __init__(self, database, allowed_business_ids):
        """Scope must be set by trusted server code, never by the agent itself."""
        self.database = database
        self.business_ids = tuple(uuid_string(v) for v in allowed_business_ids)
        if not self.business_ids:
            raise ValueError("At least one authorised business ID is required")

    def search_products(self, query=None, *, currency=None, max_price=None,
                        availability=None, limit=20, offset=0):
        """Return offer-level matches; one product may appear with several offers."""
        if query is not None:
            if not isinstance(query, str) or len(query) > 200:
                raise ValueError("query must contain at most 200 characters")
            query = query.strip() or None
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if type(offset) is not int or not 0 <= offset <= 10000:
            raise ValueError("offset must be between 0 and 10000")
        if currency is not None:
            if not isinstance(currency, str):
                raise ValueError("currency must be a three-letter code")
            currency = currency.upper()
            if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
                raise ValueError("currency must be a three-letter code")
        if max_price is not None:
            if currency is None:
                raise ValueError("currency is required when filtering by price")
            try:
                max_price = Decimal(str(max_price))
            except (InvalidOperation, ValueError):
                raise ValueError("max_price must be a finite non-negative number") from None
            if not max_price.is_finite() or max_price < 0 or max_price >= Decimal('1e14'):
                raise ValueError("max_price must be a finite non-negative number below 1e14")
        if availability not in (None, 'in_stock', 'out_of_stock', 'preorder', 'unknown'):
            raise ValueError("Invalid availability")

        sql = SELECT + " AND (o.expires_at IS NULL OR o.expires_at > now())\n"
        params = [list(self.business_ids)]
        # Each whitespace-separated term must occur somewhere in product text.
        # Escape LIKE metacharacters so '%' and '_' remain literal user input.
        for term in query.split() if query else ():
            literal = term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            sql += " AND concat_ws(' ', p.name, p.brand, p.description) ILIKE %s ESCAPE E'\\\\'\n"
            params.append('%' + literal + '%')
        if currency is not None:
            sql += " AND o.currency = %s\n"
            params.append(currency)
        if max_price is not None:
            sql += " AND o.price <= %s\n"
            params.append(max_price)
        if availability is not None:
            sql += " AND o.availability = %s\n"
            params.append(availability)
        sql += " ORDER BY p.name, p.id, o.id LIMIT %s OFFSET %s"
        params += [limit + 1, offset]
        rows = self.database.fetch(sql, params)
        return {
            'query': query, 'results': [self._offer(r) for r in rows[:limit]],
            'has_more': len(rows) > limit,
            'next_offset': offset + limit if len(rows) > limit else None,
            'checked_at': datetime.now(timezone.utc).isoformat(),
        }

    def get_offer(self, offer_id):
        """Read stored details. Expired offers are explicitly labelled, not hidden."""
        offer_id = uuid_string(offer_id)
        rows = self.database.fetch(SELECT + ' AND o.id = %s::uuid',
                                   [list(self.business_ids), offer_id])
        if not rows:
            # Missing, inactive and unauthorised offers share the same response.
            return {'found': False, 'offer_id': offer_id}
        return {'found': True, 'offer': self._offer(rows[0]),
                'checked_at': datetime.now(timezone.utc).isoformat()}

    @staticmethod
    def _offer(row):
        result = json_value(dict(row))
        result['freshness'] = ('expired' if row['expired'] else
                               'unknown' if row['expires_at'] is None else 'within_validity')
        return result
