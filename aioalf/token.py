#
# encoding: utf-8
from datetime import datetime, timedelta


class TokenError(Exception):

    def __init__(self, message, response_status, response_text):
        super(TokenError, self).__init__(message)
        self.response_status = response_status
        self.response_text = response_text


class TokenHTTPError(TokenError):

    def __str__(self):
        err = super(TokenError, self).__str__()

        if self.response_text:
            return '%s, StatusCode: %d, Body: %s' % (
                err, self.response_status, self.response_text)

        return err


class Token(object):

    def __init__(self, access_token='', expires_in=0):
        self.access_token = access_token
        self._expires_in = expires_in

        self._expires_on = datetime.now() + timedelta(seconds=self._expires_in)

    def is_valid(self):
        return self._expires_on > datetime.now()
