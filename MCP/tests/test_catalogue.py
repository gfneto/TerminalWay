import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from terminalway import Catalogue

BID = '11111111-1111-1111-1111-111111111111'
OID = '22222222-2222-2222-2222-222222222222'

class FakeDatabase:
    def __init__(self, rows=()): self.rows = list(rows); self.calls = []
    def fetch(self, sql, params): self.calls.append((sql, params)); return self.rows

class Tests(unittest.TestCase):
    def test_scope_required(self):
        with self.assertRaises(ValueError): Catalogue(FakeDatabase(), [])
    def test_query_bound_not_interpolated(self):
        db = FakeDatabase(); c = Catalogue(db, [BID])
        c.search_products("coffee%'", currency='gbp', max_price='10')
        sql, args = db.calls[0]
        self.assertNotIn("coffee", sql)
        self.assertEqual(args[0], [BID])
        self.assertEqual(args[1], "%coffee\\%'%")
        self.assertIn('GBP', args)
        self.assertIn(Decimal('10'), args)
    def test_invalid_filters_do_not_query(self):
        db = FakeDatabase(); c = Catalogue(db, [BID])
        for filters in [{'max_price':'10'}, {'currency':'GBP','max_price':'NaN'},
                        {'currency':'GBP','max_price':'-1'}, {'limit':101}, {'offset':-1}]:
            with self.assertRaises(ValueError): c.search_products('coffee', **filters)
        self.assertEqual(db.calls, [])
    def test_search_pagination_and_expiry_filter(self):
        row = {'price':Decimal('7.9000'), 'expired':False, 'expires_at':None, 'offer_id':UUID(OID)}
        db = FakeDatabase([row, row]); c = Catalogue(db, [BID])
        r = c.search_products('coffee', limit=1)
        self.assertTrue(r['has_more']); self.assertEqual(r['next_offset'],1)
        self.assertEqual(r['results'][0]['freshness'],'unknown')
        self.assertEqual(r['results'][0]['price'],'7.9000')
        self.assertIn('o.expires_at > now()', db.calls[0][0])
    def test_search_without_query_lists_offers(self):
        row = {'price':Decimal('7.90'), 'expired':False, 'expires_at':None, 'offer_id':UUID(OID)}
        db = FakeDatabase([row]); c = Catalogue(db, [BID])
        result = c.search_products()
        sql, params = db.calls[0]
        self.assertIsNone(result['query'])
        self.assertEqual(len(result['results']), 1)
        self.assertNotIn('ILIKE', sql)
        self.assertEqual(params, [[BID], 21, 0])

    def test_blank_query_lists_offers(self):
        db = FakeDatabase(); c = Catalogue(db, [BID])
        c.search_products('   ')
        self.assertNotIn('ILIKE', db.calls[0][0])
    def test_get_offer_expired_and_missing(self):
        row = {'expired':True, 'expires_at':datetime.now(timezone.utc)}
        db = FakeDatabase([row]); c = Catalogue(db,[BID])
        self.assertEqual(c.get_offer(OID)['offer']['freshness'],'expired')
        self.assertEqual(db.calls[0][1], [[BID],OID])
        db.rows=[]; self.assertFalse(c.get_offer(OID)['found'])
    def test_invalid_offer_uuid(self):
        db=FakeDatabase(); c=Catalogue(db,[BID])
        with self.assertRaises(ValueError): c.get_offer("' OR 1=1")
        self.assertEqual(db.calls,[])

if __name__ == '__main__': unittest.main()
