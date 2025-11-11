#!/usr/bin/env python3
import asyncio
import aiohttp
from aiohttp import web

BACKEND_URL = "http://127.0.0.1:8001"
FRONTEND_URL = "http://127.0.0.1:3000"

async def proxy_handler(request):
    """Proxy requests to backend or frontend"""
    try:
        # API requests go to backend
        if request.path.startswith('/api'):
            target_url = f"{BACKEND_URL}{request.path_qs}"
        else:
            # Everything else goes to frontend
            target_url = f"{FRONTEND_URL}{request.path_qs}"
        
        # Forward request
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=target_url,
                headers=request.headers,
                data=await request.read(),
                allow_redirects=False
            ) as resp:
                # Return response
                return web.Response(
                    body=await resp.read(),
                    status=resp.status,
                    headers=resp.headers
                )
    except Exception as e:
        return web.Response(text=f"Proxy error: {e}", status=502)

app = web.Application()
app.router.add_route('*', '/{path:.*}', proxy_handler)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
