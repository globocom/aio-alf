import asyncio
import webbrowser
import random
from urllib.parse import quote
from asyncio import Lock
from aiohttp import web
from aioalf.client import Client
from aioalf.manager import TokenManager


DEFAULT_PAGE = """<!DOCTYPE html><html><head><script>window.location = window.location.href.replace('#', '?');</script></head><body></body></html>"""  # noqa

CLOSE_PAGE = """<!DOCTYPE html><html><head></head><body><script>window.close();</script>
<h2 style="text-align: center;">
    Login successful.
    You can close this window.
</h2></body></html>
"""


class TokenStorage:

    def __init__(self):
        self.token = None

    def save(self, token):
        self.token = token

    def load(self):
        return self.token

    def clean(self):
        self.token = None


async def _run_web_server(port_range):
    async def token_handler(request):
        if 'access_token' not in request.query:
            return web.Response(body=DEFAULT_PAGE, content_type='text/html')

        token = {
            'access_token': request.query.get('access_token'),
            'token_type': request.query.get('token_type'),
            'expires_in': request.query.get('expires_in')
        }

        request.app['token_waiter'].set_result(token)

        return web.Response(body=CLOSE_PAGE, content_type='text/html')

    loop = asyncio.get_event_loop()

    app = web.Application()
    app['token_waiter'] = loop.create_future()
    app['port'] = random.randint(*port_range)

    app.router.add_get('/', token_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', app['port'])
    await site.start()
    return app, site


class OAuthImplictTokenManager(TokenManager):

    app = None
    site = None
    browser_has_been_opened = False
    storage = None

    def __init__(self, token_endpoint,
                 client_id, client_secret, http_options=None):
        self._token_endpoint = token_endpoint
        self._client_id = client_id
        self._client_secret = client_secret
        self._http_options = http_options if http_options else {}
        self._token_lock = Lock()

    def _shall_open_browser(cls):
        if not cls.browser_has_been_opened:
            cls.browser_has_been_opened = True
            return True
        else:
            return False

    async def get_token(self):
        async with self._token_lock:
            token = await self._retrieve_token()
            self.storage.save(token)
            return token

    def reset_token(self):
        self.storage.clean()

    def _get_stored_token(self):
        return self.storage.load()

    async def _retrieve_token(self):
        token = self._get_stored_token()
        if token:
            return token

        token = await self._ask_for_token()
        return token.get('access_token')

    async def _ask_for_token(self):
        token_url_template = (
            "{}/authorize?response_type=token&client_id={}&redirect_uri={}")

        token_url = token_url_template.format(
            self._token_endpoint,
            quote(self._client_id),
            quote("http://localhost:%d" % self.app['port']),
        )

        if self._shall_open_browser():
            webbrowser.open(token_url)

        result = None
        try:
            result = await self.app['token_waiter']
        except asyncio.CancelledError:
            await self.site.stop()
            return {'error': 'cancelled'}
        finally:
            await self.site.stop()
            return result


async def use_implicit_flow(token_storage, port_range=(32000, 32009)):
    app, site = await _run_web_server(port_range)
    OAuthImplictTokenManager.app = app
    OAuthImplictTokenManager.site = site
    OAuthImplictTokenManager.storage = token_storage
    Client.token_manager_class = OAuthImplictTokenManager
