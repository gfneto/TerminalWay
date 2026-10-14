import argparse
import json
import os
from .catalogue import Catalogue
from .database import Database

parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest='command', required=True)
search = sub.add_parser('search')
search.add_argument('query')
search.add_argument('--currency')
search.add_argument('--max-price')
search.add_argument('--availability', choices=['in_stock', 'out_of_stock', 'preorder', 'unknown'])
search.add_argument('--limit', type=int, default=20)
search.add_argument('--offset', type=int, default=0)
offer = sub.add_parser('offer')
offer.add_argument('offer_id')
args = parser.parse_args()
try:
    ids = [v.strip() for v in os.environ['ALLOWED_BUSINESS_IDS'].split(',') if v.strip()]
    catalogue = Catalogue(Database(), ids)
    if args.command == 'search':
        result = catalogue.search_products(args.query, currency=args.currency,
            max_price=args.max_price, availability=args.availability,
            limit=args.limit, offset=args.offset)
    else:
        result = catalogue.get_offer(args.offer_id)
    print(json.dumps(result, indent=2))
except (ValueError, KeyError) as exc:
    parser.exit(2, f'Configuration or input error: {exc}\n')
except Exception:
    # Do not print raw connection exceptions: they can contain sensitive details.
    parser.exit(1, 'Database operation failed. Check AWS permissions, connectivity and TLS configuration.\n')
