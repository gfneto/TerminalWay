"""TerminalWay MCP server: two read-only tools backed by Aurora."""
import argparse
import asyncio
import json
import logging
import os
import secrets
import sys
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from .catalogue import Catalogue
from .database import Database

logger = logging.getLogger(__name__)


class BearerGate:
    """Require one of the separately revocable client bearer tokens."""
    def __init__(self, app, tokens):
        self.app = app
        values = (tokens,) if isinstance(tokens, str) else tokens.values()
        self.tokens = tuple(token.encode('ascii') for token in values)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        if scope['path'] == '/health' and scope['method'] == 'GET':
            await send({'type': 'http.response.start', 'status': 200,
                        'headers': [(b'content-type', b'application/json')]})
            return await send({'type': 'http.response.body', 'body': b'{"status":"ok"}'})
        headers = {k.lower(): v for k, v in scope.get('headers', [])}
        supplied = headers.get(b'authorization', b'')
        authorised = 0
        for token in self.tokens:
            authorised |= secrets.compare_digest(supplied, b'Bearer ' + token)
        if not authorised:
            await send({'type':'http.response.start','status':401,
                        'headers':[(b'content-type',b'application/json'),
                                   (b'www-authenticate',b'Bearer')]})
            return await send({'type':'http.response.body','body':b'{"error":"unauthorized"}'})
        return await self.app(scope, receive, send)


def create_server(catalogue, allowed_hosts=None, allowed_origins=None):
    mcp = FastMCP(
        'TerminalWay',
        instructions='Read-only product and offer lookup. Prices are decimal strings. '
                     'Check freshness and expiry; stored inventory is not a stock reservation.',
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts or ['127.0.0.1:*','localhost:*','[::1]:*'],
            allowed_origins=allowed_origins or ['http://localhost:*','http://127.0.0.1:*']),
    )
    annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                  idempotentHint=True, openWorldHint=False)

    @mcp.tool(annotations=annotations)
    async def search_products(query: str | None = None, currency: str | None = None,
                              max_price: str | None = None,
                              availability: str | None = None,
                              limit: int = 20, offset: int = 0) -> dict:
        """Find offer-level product matches by name, brand or description. Omit
        query to list offers without a text filter.

        All whitespace-separated terms must match when query is provided.
        max_price is a decimal string and requires currency (e.g. GBP).
        availability: in_stock, out_of_stock, preorder or unknown. Explicitly
        expired offers are excluded; unknown expiry does not guarantee freshness.
        limit 1–100, offset 0–10000.
        Returns offer_id values for get_offer. No currency conversion.
        """
        try:
            return await asyncio.to_thread(catalogue.search_products, query,
                currency=currency, max_price=max_price, availability=availability,
                limit=limit, offset=offset)
        except ValueError as exc:
            raise ValueError(str(exc)) from None
        except Exception:
            logger.exception('search_products failed')
            raise RuntimeError('Catalogue query failed; check server logs.') from None

    @mcp.tool(annotations=annotations)
    async def get_offer(offer_id: str) -> dict:
        """Read a stored offer by UUID, including price, quantity and expiry.

        Missing, unauthorised and inactive offers return found=false. Expired
        offers may be returned with freshness=expired. This does not contact the
        merchant live, confirm stock, reserve a product or place an order.
        """
        try:
            return await asyncio.to_thread(catalogue.get_offer, offer_id)
        except ValueError as exc:
            raise ValueError('offer_id must be a valid UUID') from None
        except Exception:
            logger.exception('get_offer failed')
            raise RuntimeError('Offer query failed; check server logs.') from None
    return mcp


def load_api_tokens():
    configured = os.environ.get('MCP_API_TOKENS')
    legacy_token = os.environ.get('MCP_API_TOKEN')
    if configured and legacy_token:
        raise ValueError('Set MCP_API_TOKENS or MCP_API_TOKEN, not both')
    if configured:
        tokens = json.loads(configured)
        if not isinstance(tokens, dict) or not tokens:
            raise ValueError('MCP_API_TOKENS must be a non-empty JSON object of client names to tokens')
    elif legacy_token:
        tokens = {'legacy-client': legacy_token}
    else:
        tokens = {}
    if any(not isinstance(name, str) or not name.strip()
           or not isinstance(token, str) or len(token) < 32 or not token.isascii()
           for name, token in tokens.items()):
        raise ValueError('Each MCP API token needs a client name and at least 32 ASCII characters')
    return tokens


def main():
    logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
    parser = argparse.ArgumentParser()
    parser.add_argument('--transport', choices=['stdio','http'], default='stdio')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    ids = [v.strip() for v in os.environ.get('ALLOWED_BUSINESS_IDS','').split(',') if v.strip()]
    try:
        catalogue = Catalogue(Database(), ids)
        hosts = [v.strip() for v in os.environ.get('MCP_ALLOWED_HOSTS','').split(',') if v.strip()]
        origins = [v.strip() for v in os.environ.get('MCP_ALLOWED_ORIGINS','').split(',') if v.strip()]
        server = create_server(catalogue, hosts or None, origins or None)
        if args.transport == 'stdio':
            server.run(transport='stdio')
        else:
            tokens = load_api_tokens()
            if not tokens:
                parser.error('HTTP requires MCP_API_TOKENS with at least one client token')
            import uvicorn
            app = BearerGate(server.streamable_http_app(), tokens)
            uvicorn.run(app, host=args.host, port=args.port, access_log=False)
    except (ValueError, KeyError) as exc:
        parser.exit(2, f'Configuration error: {exc}\n')

if __name__ == '__main__':
    main()
