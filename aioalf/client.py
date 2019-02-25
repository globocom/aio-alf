#
# encoding: utf-8
import logging

from aiohttp import ClientSession
from aioalf.manager import TokenManager, TokenError
from aioalf.token import TOKEN_FILTER

BAD_TOKEN = 401

logger = logging.getLogger(__name__)


class Client(object):

    token_manager_class = TokenManager

    def __init__(self, client_id, client_secret,
                 token_endpoint, http_options=None,
                 scope=None):
        http_options = http_options is None and {} or http_options
        self._http_client = ClientSession()
        self._token_manager = self.token_manager_class(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret,
            http_options=http_options,
            scope=scope)

    async def close(self):
        await self._http_client.close()

    async def request(self, method, url, **kwargs):
        try:
            response = await self._authorized_fetch(method,
                                                    url,
                                                    **kwargs)
            if response.status != BAD_TOKEN:
                return response

            await self._token_manager.reset_token()
            response = await self._authorized_fetch(method,
                                                    url,
                                                    **kwargs)
            return response

        except TokenError:
            await self._token_manager.reset_token()
            raise

    async def _authorized_fetch(self, method, url, **kwargs):
        access_token = await self._token_manager.get_token()

        auth_headers = {'Authorization': 'Bearer {}'.format(access_token)}
        if 'headers' in kwargs:
            kwargs['headers'].update(auth_headers)
        else:
            kwargs['headers'] = auth_headers

        logger.debug('Request: %s %s', method, url)
        for header in kwargs.get('headers'):
            if header.lower() == 'authorization':
                authorization_data = kwargs.get('headers', {}).get(header)
                matches = TOKEN_FILTER.match(authorization_data)
                if matches:
                    logger.debug(('Header {}: {}<...>{}').format(header,
                                                                 matches.group('start'),
                                                                 matches.group('end')))
                continue
            logger.debug('Header %s: %s', header, kwargs.get('headers').get(header))

        return await self._http_client.request(method, url, **kwargs)

    def __enter__(self):
        raise TypeError("Use async with instead.")

    def __exit__(self, type, value, traceback):
        pass  # pragma: no cover

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.close()
