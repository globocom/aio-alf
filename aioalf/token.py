#
# encoding: utf-8
import re
from datetime import datetime, timedelta

TOKEN_FILTER = re.compile(r'^(?P<start>.*\ .{5}).*(?P<end>.{2})$')


class TokenError(Exception):

    def __init__(self, message):
        super(TokenError, self).__init__(message)


class TokenHTTPError(TokenError):

    def __init__(self, message, response_status=None, response_text=None):
        super().__init__(message)
        self.response_status = response_status
        self.response_text = response_text

    def __str__(self):
        err = super().__str__()

        if self.response_text:
            return '%s, StatusCode: %d, Body: %s' % (
                err, self.response_status, self.response_text)

        return err


class Token(object):

    def __init__(self, access_token='', expires_in=0):
        self.access_token = access_token
        self._expires_in = expires_in

        self.expires_on = datetime.utcnow() + timedelta(
            seconds=int(self._expires_in))

    def is_valid(self):
        return self.expires_on > datetime.utcnow()
