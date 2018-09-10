# -*- coding: utf-8 -*-

from unittest import TestCase
from asyncio import Future
from asynctest import patch, CoroutineMock, Mock
from . import AsyncTestCase
from aiohttp.test_utils import unittest_run_loop
from aioalf.implicit_manager import OAuthImplictTokenManager, TokenStorage


class TestImplicitTokenManager(AsyncTestCase):

    async def setUpAsync(self):
        self.end_point = 'http://endpoint'
        self.client_id = 'client_id'
        self.client_secret = ''
        self.manager = OAuthImplictTokenManager(self.end_point,
                                                self.client_id,
                                                self.client_secret)
        self._fake_fetch = CoroutineMock()
        self.manager._fetch = self._fake_fetch

    @unittest_run_loop
    async def test_can_load_and_save_token_from_storage(self):
        storage = Mock()
        storage.load.return_value = '1234'
        self.manager.storage = storage

        token = await self.manager.get_token()

        self.assertEqual(token, '1234')
        storage.load.assert_called_once()
        storage.save.assert_called_once()

    @unittest_run_loop
    async def test_can_reset_token_from_storage(self):
        storage = Mock()
        self.manager.storage = storage

        self.manager.reset_token()

        storage.clean.assert_called_once()

    @patch('webbrowser.open')
    @unittest_run_loop
    async def test_can_open_browser(self, browser_open_mock):
        storage = Mock()
        storage.load.return_value = None

        site = Mock()
        site.stop = CoroutineMock()
        token_waiter = Future()
        token_waiter.set_result({'access_token': '1234'})
        app = {'port': 30000, 'token_waiter': token_waiter}

        self.manager.storage = storage
        self.manager.app = app
        self.manager.site = site

        token = await self.manager.get_token()

        self.assertEqual(token, '1234')
        browser_open_mock.assert_called_with('http://endpoint/authorize?response_type=token&client_id=client_id&redirect_uri=http%3A//localhost%3A30000')  # noqa

    @patch('webbrowser.open')
    @unittest_run_loop
    async def test_can_open_browser_with_scope(self, browser_open_mock):
        self.manager = OAuthImplictTokenManager(self.end_point,
                                                self.client_id,
                                                self.client_secret,
                                                scope="user")
        storage = Mock()
        storage.load.return_value = None

        site = Mock()
        site.stop = CoroutineMock()
        token_waiter = Future()
        token_waiter.set_result({'access_token': '1234'})
        app = {'port': 30000, 'token_waiter': token_waiter}

        self.manager.storage = storage
        self.manager.app = app
        self.manager.site = site

        token = await self.manager.get_token()

        self.assertEqual(token, '1234')
        browser_open_mock.assert_called_with('http://endpoint/authorize?response_type=token&client_id=client_id&redirect_uri=http%3A//localhost%3A30000&scope=user')  # noqa

    @patch('webbrowser.open')
    @unittest_run_loop
    async def test_can_open_browser_with_scopes(self, browser_open_mock):
        self.manager = OAuthImplictTokenManager(self.end_point,
                                                self.client_id,
                                                self.client_secret,
                                                scope=["user", "user:admin", "specialScope"])
        storage = Mock()
        storage.load.return_value = None

        site = Mock()
        site.stop = CoroutineMock()
        token_waiter = Future()
        token_waiter.set_result({'access_token': '1234'})
        app = {'port': 30000, 'token_waiter': token_waiter}

        self.manager.storage = storage
        self.manager.app = app
        self.manager.site = site

        token = await self.manager.get_token()

        self.assertEqual(token, '1234')
        browser_open_mock.assert_called_with('http://endpoint/authorize?response_type=token&client_id=client_id&redirect_uri=http%3A//localhost%3A30000&scope=user%20user%3Aadmin%20specialScope')  # noqa


class TestTokenStorage(TestCase):

    def test_can_save_token(self):
        storage = TokenStorage()
        storage.save('1234')

        self.assertEqual(storage.token, '1234')

    def test_can_load_token(self):
        storage = TokenStorage()
        storage.token = '1234'
        token = storage.load()

        self.assertEqual(token, '1234')

    def test_can_clean_token(self):
        storage = TokenStorage()
        storage.save('1234')

        self.assertEqual(storage.token, '1234')

        storage.clean()

        self.assertEqual(storage.token, None)
