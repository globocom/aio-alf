# -*- coding: utf-8 -*-

from asynctest import patch, CoroutineMock
from . import AsyncTestCase

from aiohttp.test_utils import unittest_run_loop
from aioalf.manager import TokenManager, TokenHTTPError, TokenError
from aioalf.client import Client


class TestClient(AsyncTestCase):

    end_point = 'http://endpoint/token'
    resource_url = 'http://api/some/resource'

    def test_client_should_have_a_variable_with_a_token_manager_class(self):
        self.assertEquals(Client.token_manager_class, TokenManager)

    @unittest_run_loop
    async def test_manager_should_be_a_token_manager_class(self):
        client = Client(token_endpoint=self.end_point,
                        client_id='client-id', client_secret='client_secret')

        self.assertTrue(
            isinstance(client._token_manager, client.token_manager_class)
        )

    @unittest_run_loop
    @patch('aioalf.client.Client.close')
    async def test_async_with_closes_client(self, close_mock):
        async with Client(token_endpoint=self.end_point,
                        client_id='client-id', client_secret='client_secret') as client:
            pass

        close_mock.assert_called_once()

    @unittest_run_loop
    @patch('aioalf.client.TokenManager')
    async def test_should_return_a_good_request(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('aioalf.client.Client._authorized_fetch') as _authorized_fetch:

            _authorized_fetch.return_value = CoroutineMock(status=200)
            response = await self._request(Manager)
            self.assertEqual(response.status, 200)
            self.assertEqual(_authorized_fetch.call_count, 1)
            self.assertEqual(manager.reset_token.call_count, 0)

    @unittest_run_loop
    @patch('aioalf.client.TokenManager')
    async def test_should_return_a_bad_request(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('aioalf.client.Client._authorized_fetch') as _authorized_fetch:

            _authorized_fetch.return_value = CoroutineMock(status=400)
            response = await self._request(Manager)
            self.assertEqual(response.status, 400)
            self.assertEqual(_authorized_fetch.call_count, 1)
            self.assertEqual(manager.reset_token.call_count, 0)

    @unittest_run_loop
    @patch('aioalf.client.TokenManager')
    async def test_should_retry_a_bad_token_request_once(self, Manager):
        self._fake_manager(Manager, has_token=False)

        with patch('aioalf.client.Client._authorized_fetch') as _authorized_fetch:

            _authorized_fetch.return_value = CoroutineMock(status=401)
            response = await self._request(Manager)
            self.assertEqual(response.status, 401)
            self.assertEqual(_authorized_fetch.call_count, 2)

    @unittest_run_loop
    @patch('aioalf.client.TokenManager')
    async def test_should_reset_token_when_token_fails(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('aioalf.client.Client._authorized_fetch') as _authorized_fetch:

            _authorized_fetch.return_value = CoroutineMock(status=401)
            response = await self._request(Manager)
            self.assertEqual(response.status, 401)
            self.assertEqual(manager.reset_token.call_count, 1)

    @unittest_run_loop
    @patch('aioalf.client.TokenManager')
    async def test_should_reset_token_when_gets_a_token_error(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('aioalf.client.Client._authorized_fetch') as _authorized_fetch:

            _authorized_fetch.side_effect = TokenHTTPError('boom', 401, 'boom')
            try:
                await self._request(Manager)
            except TokenError as e:
                if hasattr(e, 'message'):
                    self.assertEqual(e.message, 'boom')
                elif hasattr(e, 'response_text'):
                    self.assertEqual(e.response_text, 'boom')
                else:
                    assert False, 'Should not have got this far'
                self.assertEqual(_authorized_fetch.call_count, 1)
                self.assertEqual(manager.reset_token.call_count, 1)
            else:
                assert False, 'Should not have got this far'

    async def _request(self, manager):
        class ClientTest(Client):
            token_manager_class = manager

        client = ClientTest(
            token_endpoint=self.end_point,
            client_id='client_id',
            client_secret='client_secret')

        return await client.request('GET', self.resource_url)

    def _fake_manager(self, Manager, has_token=True,
                      access_token='', code=200):
        if not isinstance(access_token, list):
            access_token = [access_token]

        access_token.reverse()

        manager = CoroutineMock()
        manager._has_token.return_value = has_token
        manager.get_token.return_value = CoroutineMock(access_token[0])
        manager.request_token.return_value = CoroutineMock(
            code=code,
            error=(code == 200 and None or Exception('error'))
        )

        Manager.return_value = manager

        return manager
