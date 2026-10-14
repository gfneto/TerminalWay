"""Protocol smoke client; no LLM required. Never prints credentials."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

async def exercise(session, args):
    await session.initialize()
    tools = await session.list_tools()
    print('Tools:', ', '.join(t.name for t in tools.tools))
    if args.offer_id:
        result = await session.call_tool('get_offer', {'offer_id':args.offer_id})
    else:
        params = {}
        if args.query is not None:
            params['query'] = args.query
        if args.currency: params['currency'] = args.currency
        if args.max_price: params['max_price'] = args.max_price
        params['limit'] = args.limit
        params['offset'] = args.offset
        result = await session.call_tool('search_products', params)
    print(json.dumps(result.model_dump(mode='json'), indent=2))
    if result.isError:
        return False
    return True

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url', help='Omit for a local stdio subprocess')
    parser.add_argument('--query')
    parser.add_argument('--currency')
    parser.add_argument('--max-price')
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--offer-id')
    args=parser.parse_args()
    if args.url:
        if not args.url.startswith('https://') and not args.url.startswith(('http://127.0.0.1:', 'http://localhost:')):
            parser.error('Use HTTPS for remote HTTP connections')
        token=os.environ['MCP_API_TOKEN']
        async with streamablehttp_client(args.url, headers={'Authorization':'Bearer '+token}) as (read, write, _):
            async with ClientSession(read,write) as session:
                succeeded = await exercise(session,args)
    else:
        params=StdioServerParameters(command=sys.executable,
            args=['-m','terminalway.mcp_server'], env=dict(os.environ),
            cwd=str(Path(__file__).resolve().parent))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                succeeded = await exercise(session,args)
    if not succeeded:
        raise SystemExit(1)

if __name__=='__main__': asyncio.run(main())
