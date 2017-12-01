#
# encoding: utf-8
import logging

from aiohttp import ClientSession
from aioalf.manager import TokenManager, TokenError

BAD_TOKEN = 401

logger = logging.getLogger(__name__)


class Client(object):

    token_manager_class = TokenManager

    def __init__(self, client_id, client_secret,
                 token_endpoint, http_options=None):
        http_options = http_options is None and {} or http_options
        self._http_client = ClientSession()
        self._token_manager = self.token_manager_class(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret,
            http_options=http_options)

    async def request(self, method, url, **kwargs):
        try:
            response = await self._authorized_fetch(method,
                                                    url,
                                                    **kwargs)
            if response.status != BAD_TOKEN:
                return response

            self._token_manager.reset_token()
            response = await self._authorized_fetch(method,
                                                    url,
                                                    **kwargs)
            return response

        except TokenError:
            self._token_manager.reset_token()
            raise

    async def _authorized_fetch(self, method, url, **kwargs):
        access_token = await self._token_manager.get_token()

        kwargs.update('headers', {
            'Authorization': 'Bearer {}'.format(access_token)
        })

        logger.debug('Request: %s %s', method, url)
        for header in kwargs.get('headers'):
            logger.debug('Header %s: %s', header, kwargs.get('headers').get(header))

        return await self._http_client.request(method, url, **kwargs)
