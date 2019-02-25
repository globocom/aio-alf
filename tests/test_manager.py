# -*- coding: utf-8 -*-

from asynctest import patch, CoroutineMock
from . import AsyncTestCase, make_response
from aiohttp.test_utils import unittest_run_loop
from aioalf.manager import TokenManager, TokenHTTPError, Token, TokenError


class TestTokenManager(AsyncTestCase):

    async def setUpAsync(self):
        self.end_point = 'http://endpoint/token'
        self.client_id = 'client_id'
        self.client_secret = 'client_secret'
        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret)
        self._fake_fetch = CoroutineMock()
        self.manager._fetch = self._fake_fetch

    def test_should_start_with_no_token(self):
        self.assertFalse(self.manager._has_token())

    def test_should_detect_expired_token(self):
        self.manager._token = Token('', expires_in=0)
        self.assertFalse(self.manager._has_token())

    def test_should_respect_valid_token(self):
        self.manager._token = Token('', expires_in=10)
        self.assertTrue(self.manager._has_token())

    @unittest_run_loop
    async def test_should_reset_token(self):
        self._fake_fetch.return_value = {
            'access_token': 'accesstoken',
            'expires_in': 10,
        }
        await self.manager.reset_token()

        self.assertEqual(self.manager._token.access_token, 'accesstoken')
        self.assertEqual(self.manager._token._expires_in, 10)

    @unittest_run_loop
    async def test_should_be_able_to_request_a_new_token(self):
        self._fake_fetch.return_value = {
            'access_token': 'accesstoken',
            'expires_in': 10,
        }

        await self.manager._request_token()

        self._fake_fetch.assert_called_with(
            url=self.end_point,
            method="POST",
            auth=(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'},
        )

    @unittest_run_loop
    async def test_should_raise_token_error_for_bad_token(self):
        self._fake_fetch.side_effect = TokenHTTPError('error', 500, 'fail')

        with self.assertRaises(TokenError) as context:
            await self.manager._request_token()

        self.assertEqual(context.exception.response_status, 500)

    @unittest_run_loop
    async def test_get_token_data_should_obtain_new_token(self):
        _request_token = CoroutineMock()
        _request_token.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 10,
        }
        self.manager._request_token = _request_token
        await self.manager._get_token_data()

        self.assertTrue(_request_token.called)

    @unittest_run_loop
    async def test_update_token_should_set_a_token_with_data_retrieved(self):
        _request_token = CoroutineMock()
        _request_token.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 10,
        }
        self.manager._request_token = _request_token
        self.manager._token = Token('access_token', expires_in=100)

        await self.manager._update_token()

        self.assertTrue(_request_token.called)

        self.assertEqual(self.manager._token.access_token, 'new_access_token')
        self.assertEqual(self.manager._token._expires_in, 10)

    @unittest_run_loop
    async def test_should_return_token_value(self):
        self.manager._token = Token('access_token', expires_in=10)
        token = await self.manager.get_token()
        self.assertEqual(token, 'access_token')

    @unittest_run_loop
    @patch('aioalf.manager.TokenManager._update_token')
    @patch('aioalf.manager.TokenManager._has_token')
    async def test_get_token_should_request_a_new_token_if_do_not_have_a_token(
            self, _has_token, _update_token):

        _has_token.return_value = False

        def set_token():
            self.manager._token = Token('access_token', expires_in=100)
        _update_token.side_effect = set_token

        token = await self.manager.get_token()

        self.assertEqual(token, 'access_token')
        self.assertTrue(_update_token.called)


class ClientSessionMock(CoroutineMock):

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        pass


class TestTokenManagerHTTP(AsyncTestCase):

    async def setUpAsync(self):
        self.end_point = 'http://endpoint/token'
        self.client_id = 'client_id'
        self.client_secret = 'client_secret'
        self.http_options = {'timeout': 2}

    @patch('aioalf.manager.ClientSession')
    @unittest_run_loop
    async def test_work_with_no_http_options(self, client_session_mock):
        _fake_fetch = CoroutineMock()
        client_mock = ClientSessionMock()
        client_mock.request = _fake_fetch
        client_session_mock.return_value = client_mock

        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret)

        fake_response = make_response(
            self.loop,
            'POST',
            'http://localhost/token',
            data='{"access_token":"access","expires_in":10}',
            content_type='application/json'
        )
        _fake_fetch.return_value = fake_response

        await self.manager._request_token()
        request_kwargs = _fake_fetch.call_args[1]
        assert 'timeout' not in request_kwargs

    @patch('aioalf.manager.ClientSession')
    @unittest_run_loop
    async def test_should_use_http_options(self, client_session_mock):
        _fake_fetch = CoroutineMock()
        client_mock = ClientSessionMock()
        client_mock.request = _fake_fetch
        client_session_mock.return_value = client_mock

        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret,
                                    self.http_options)

        fake_response = make_response(
            self.loop,
            'POST',
            'http://localhost/token',
            data='{"access_token":"access","expires_in":10}',
            content_type='application/json'
        )
        _fake_fetch.return_value = fake_response

        await self.manager._request_token()
        request_kwargs = _fake_fetch.call_args[1]
        self.assertEqual(request_kwargs['timeout'], 2)
        self.assertEqual(request_kwargs.get('headers').get('Authorization'),
                         'Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ=')

    @patch('aioalf.manager.ClientSession')
    @unittest_run_loop
    async def test_can_use_simple_scope(self, client_session_mock):
        _fake_fetch = CoroutineMock()
        client_mock = ClientSessionMock()
        client_mock.request = _fake_fetch
        client_session_mock.return_value = client_mock

        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret,
                                    self.http_options,
                                    scope="user")

        fake_response = make_response(
            self.loop,
            'POST',
            'http://localhost/token',
            data='{"access_token":"access","expires_in":10}',
            content_type='application/json'
        )
        _fake_fetch.return_value = fake_response

        await self.manager._request_token()
        request_kwargs = _fake_fetch.call_args[1]
        self.assertEqual(request_kwargs['timeout'], 2)
        self.assertEqual(request_kwargs.get('headers').get('Authorization'),
                         'Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ=')
        self.assertEqual(request_kwargs.get('data').get('scope'),
                         'user')

    @patch('aioalf.manager.ClientSession')
    @unittest_run_loop
    async def test_can_use_multiple_scopes(self, client_session_mock):
        _fake_fetch = CoroutineMock()
        client_mock = ClientSessionMock()
        client_mock.request = _fake_fetch
        client_session_mock.return_value = client_mock

        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret,
                                    self.http_options,
                                    scope=["user", "user:admin", "specialScope"])

        fake_response = make_response(
            self.loop,
            'POST',
            'http://localhost/token',
            data='{"access_token":"access","expires_in":10}',
            content_type='application/json'
        )
        _fake_fetch.return_value = fake_response

        await self.manager._request_token()
        request_kwargs = _fake_fetch.call_args[1]
        self.assertEqual(request_kwargs['timeout'], 2)
        self.assertEqual(request_kwargs.get('headers').get('Authorization'),
                         'Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ=')
        self.assertEqual(request_kwargs.get('data').get('scope'),
                         'user user:admin specialScope')
