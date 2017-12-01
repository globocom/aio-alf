# -*- coding: utf-8 -*-
from base64 import b64encode
from aioalf.token import Token, TokenError, TokenHTTPError
from aiohttp import ClientSession, ClientResponseError

import logging

logger = logging.getLogger(__name__)


class TokenManager(object):

    def __init__(self, token_endpoint, client_id,
                 client_secret, http_options=None):

        self._token_endpoint = token_endpoint
        self._client_id = client_id
        self._client_secret = client_secret
        self._token = Token()
        self._http_options = http_options if http_options else {}
        self._http_client = ClientSession()

    def _has_token(self):
        return self._token.is_valid()

    async def get_token(self):
        if not self._has_token():
            await self._update_token()
        return self._token.access_token

    async def _get_token_data(self):
        return await self._request_token()

    def reset_token(self):
        self._token = Token()

    async def _update_token(self):
        token_data = await self._get_token_data()
        self._token = Token(token_data.get('access_token', ''),
                            token_data.get('expires_in', 0))

    async def _request_token(self):
        if not self._token_endpoint:
            raise TokenError('Missing token endpoint')

        return await self._fetch(
            url=self._token_endpoint,
            method="POST",
            auth=(self._client_id, self._client_secret),
            data={'grant_type': 'client_credentials'}
        )

    async def _fetch(self, url, method="GET", data=None, auth=None):
        request_data = dict(
            headers={},
            data=data
        )

        if auth is not None:
            try:
                passhash = b64encode(':'.join(auth).encode('ascii'))
            except TypeError as e:
                raise TokenError(
                    'Missing credentials (client_id:client_secret)', str(e)
                )

            request_data['headers']['Authorization'] = (
                'Basic %s' % passhash.decode('utf-8')
            )

        request_data.update(self._http_options)

        logger.debug('Request: %s %s', method, url)
        for header in request_data.get('headers'):
            logger.debug('Header %s: %s', header, request_data.get('headers', {}).get(header))

        try:
            response = await self._http_client.request(method, url, **request_data)
            async with response:
                result = await response.json()
                await self._http_client.close()
                return result
        except ClientResponseError as e:
            raise TokenHTTPError('Failed to request token', e.status, e.message)
