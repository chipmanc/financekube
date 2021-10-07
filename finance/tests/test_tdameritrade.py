from unittest.mock import patch

from django.test import Client, TestCase

from finance.utils import tdameritrade
from finance.models import Option


# class MockResponse:
#     def __init__(self):
#         self.status_code = 200
#
#     def td_response(self):
#         return {
#             "week_number": 18,
#             "utc_offset": "+02:00",
#             "utc_datetime": "2020-04-30T10:48:54.398875+00:00",
#             "unixtime": 1588243734,
#             "timezone": "Europe/Rome",
#             "raw_offset": 3600,
#             "dst_until": "2020-10-25T01:00:00+00:00",
#             "dst_offset": 3600,
#             "dst_from": "2020-03-29T01:00:00+00:00",
#             "dst": True,
#             "day_of_year": 121,
#             "day_of_week": 4,
#             "datetime": "2020-04-30T12:48:54.398875+02:00",
#             "client_ip": "91.252.18.0",
#             "abbreviation": "CEST"
#         }

class TDTestCase(TestCase):
    fixtures = ['options']

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_stock_basic_data(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_stock_stddev(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_stock_option_chain(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_initial_filter(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_put_good(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_put_nogood_friday(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_put_nogood_monday(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_call_good(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_call_nogood_friday(self, requests):
        pass

    @patch('finance.utils.tdameritrade.requests.get')  # , return_value=MockResponse())
    def test_td_update_call_nogood_monday(self, requests):
        pass

    @patch('finance.utils.tdameritrade.ModelOption')
    @patch('finance.utils.tdameritrade.Stock')
    def test_td_update_expired(self, option, stock):
        pass
