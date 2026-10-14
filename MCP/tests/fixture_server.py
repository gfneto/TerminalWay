# Test-only process: never used by the normal server.
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from terminalway import Catalogue
from terminalway.mcp_server import create_server

class FakeDB:
    def fetch(self, sql, params):
        return [{'offer_id':'22222222-2222-2222-2222-222222222222',
                 'price':Decimal('7.90'), 'expired':False,
                 'expires_at':datetime.now(timezone.utc)+timedelta(hours=1)}]

if __name__=='__main__':
    create_server(Catalogue(FakeDB(),['11111111-1111-1111-1111-111111111111'])).run(transport='stdio')
