import os
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from terminalway.mcp_server import BearerGate, load_api_tokens
from client_test import exercise

class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_error_returns_failure_without_raising(self):
        class ErrorSession:
            async def initialize(self): pass
            async def list_tools(self):
                return SimpleNamespace(tools=[])
            async def call_tool(self, name, params):
                return SimpleNamespace(
                    model_dump=lambda **kwargs: {'isError': True},
                    isError=True,
                )

        args = SimpleNamespace(offer_id=None, query='coffee', currency=None,
                               max_price=None, limit=100, offset=0)
        self.assertFalse(await exercise(ErrorSession(), args))

    async def test_stdio_discovery_and_calls(self):
        root=Path(__file__).resolve().parent.parent
        env=dict(os.environ); env['PYTHONPATH']=str(root)
        params=StdioServerParameters(command=sys.executable,args=[str(root/'tests/fixture_server.py')], env=env,cwd=str(root))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                self.assertEqual({t.name for t in tools.tools},{'search_products','get_offer'})
                for t in tools.tools:
                    self.assertTrue(t.annotations.readOnlyHint)
                result=await session.call_tool('search_products',{'query':'coffee','currency':'GBP','max_price':'10'})
                self.assertFalse(result.isError)
                self.assertEqual((result.structuredContent or json.loads(result.content[0].text))['results'][0]['price'],'7.90')
                result=await session.call_tool('get_offer',{'offer_id':'22222222-2222-2222-2222-222222222222'})
                self.assertTrue((result.structuredContent or json.loads(result.content[0].text))['found'])
                bad=await session.call_tool('get_offer',{'offer_id':'invalid'})
                self.assertTrue(bad.isError)

    async def test_http_auth(self):
        called=[]
        async def app(scope,receive,send):
            called.append(True)
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        gate=BearerGate(app,'x'*32)
        async def receive(): return {'type':'http.request','body':b''}
        for token,status in [(b'',401),(b'Bearer wrong',401),(b'Bearer '+b'x'*32,200)]:
            out=[]
            async def send(event): out.append(event)
            await gate({'type':'http','path':'/mcp','method':'POST','headers':[(b'authorization',token)]},receive,send)
            self.assertEqual(out[0]['status'],status)
        self.assertEqual(len(called),1)

    def test_load_api_tokens(self):
        from unittest.mock import patch
        configured = '{"client-a":"' + 'a' * 32 + '","client-b":"' + 'b' * 32 + '"}'
        with patch.dict(os.environ, {'MCP_API_TOKENS':configured, 'MCP_API_TOKEN':''}):
            self.assertEqual(load_api_tokens(), {'client-a':'a'*32, 'client-b':'b'*32})
        with patch.dict(os.environ, {'MCP_API_TOKENS':'{"client-a":"short"}',
                                     'MCP_API_TOKEN':''}):
            with self.assertRaises(ValueError):
                load_api_tokens()

    async def test_http_auth_accepts_each_client_token(self):
        called=[]
        async def app(scope,receive,send):
            called.append(True)
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'ok'})
        gate=BearerGate(app, {'client-a':'a'*32, 'client-b':'b'*32})
        async def receive(): return {'type':'http.request','body':b''}
        for token in (b'Bearer '+b'a'*32, b'Bearer '+b'b'*32):
            out=[]
            async def send(event): out.append(event)
            await gate({'type':'http','path':'/mcp','method':'POST',
                        'headers':[(b'authorization',token)]},receive,send)
            self.assertEqual(out[0]['status'],200)
        self.assertEqual(len(called),2)
