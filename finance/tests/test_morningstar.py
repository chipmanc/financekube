from unittest.mock import patch

from django.test import Client, TestCase

from finance.utils import morningstar
from finance.models import StockSymbol


class MorningstarTestCase(TestCase):
    fixtures = ['options']

    @patch('morningstar.requests.get')  # , return_value=MockResponse())
    def test_morningstar_login(self, requests):
        pass

    @patch('morningstar.requests.get')  # , return_value=MockResponse())
    def test_morningstar_update(self, requests):
        pass

    @patch('morningstar.requests.get')  # , return_value=MockResponse())
    def test_morningstar_fair_value(self, requests):
        pass

    @patch('morningstar.requests.get')  # , return_value=MockResponse())
    def test_morningstar_fair_value_Q(self, requests):
        pass

    @patch('morningstar.requests.get')  # , return_value=MockResponse())
    def test_morningstar_stars(self, requests):
        pass

    @patch('morningstar.requests.get')  # , return_value=MockResponse())
    def test_morningstar_uncertainty(self, requests):
        pass