aio-alf |build-status|
===========

aiohttp OAuth 2 Client
---------------------

`aio-alf` is a OAuth 2 Client base on the aiohttp's AsyncHTTPClient

Features
--------

* Automatic token retrieving and renewing
* Token expiration control
* Automatic retry on status 401 (UNAUTHORIZED)

Usage
-----

Initialize the client and use it as a AsyncHTTPClient object.

.. code-block:: python

    from aioalf.client import Client
    from aioalf.httpclient import HTTPRequest

    client = Client(
        token_endpoint='http://example.com/token',
        client_id='client-id',
        client_secret='secret')

    resource_uri = 'http://example.com/resource'

    response = await client.request(
        'POST',
        resource_uri,
        data='{"name": "alf"}',
        headers={'Content-Type': 'application/json'}
    )


Alternatively one can pass directly a string to the fetch client

.. code-block:: python

    # ...
    response = await client.request(
        'POST',
        'http://example.com/resource',
        data='{"name": "alf"}',
        headers={'Content-Type': 'application/json'}
    )

Implicit Flow
-------------

Support for OAuth2 implict flow to enable it, call `use_implicit_flow` with a `TokenStorage`
object and a port range, it defaults to the range (32000, 32009).

Example:

.. code-block:: python

    await use_implicit_flow(TokenStorage(), (30000, 30009))

    async with Client(token_endpoint='https://token.endpoint',
                      client_id='glBQ3nYU/8/kaVi/bIgXGA==',
                      client_secret='') as client:
        response = await client.request('GET', 'http://example.com/resource')
        text = await response.text()
        print(response.status)

The library has a really simple in memory token storage, you should subclass and overwrite
its methods if you need to persist the token for a longer period.


How it works?
-------------

Before any request the client tries to retrieve a token on the endpoint,
expecting a JSON response with the ``access_token`` and ``expires_in`` keys.

The client keeps the token until it is expired, according to the ``expires_in``
value.

After getting the token, the request is issued with a `Bearer authorization
header <http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-7.1>`_:

.. code-block::

    GET /resource/1 HTTP/1.1
    Host: example.com
    Authorization: Bearer token

If the request fails with a 401 (UNAUTHORIZED) status, a new token is retrieved
from the endpoint and the request is retried. This happens only once, if it
fails again the error response is returned.


Troubleshooting
---------------

In case of an error retrieving a token, the error response will be returned,
the real request won't happen.


Related projects
----------------

This project tries to be an adaptation to aiohttp of
`alf <https://github.com/globocom/alf>`_


.. |build-status| image:: https://secure.travis-ci.org/globocom/aio-alf.png?branch=master
                  :target: https://travis-ci.org/globocom/aio-alf
