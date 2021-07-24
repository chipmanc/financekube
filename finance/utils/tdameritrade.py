import datetime as dt
import json
import logging
from math import sqrt
from statistics import NormalDist, StatisticsError
import time

from django.core.exceptions import ObjectDoesNotExist
import requests

from finance.models import Option as ModelOption
from finance.models import StockSymbol

logger = logging.getLogger(__name__)

ACCOUNT_ID = '275270616'
ACCESS_TYPE = 'offline'  # Use if need a new refresh token
CLIENT_ID = 'TVTMGKIMONGROXTMOXA13OSZGV5EY4BU'
REDIRECT_URI = 'http://127.0.0.1'
REFRESH_TOKEN = ('eOhX6bz9AjyKiWNiJQecRmCGKby5/RcaP6oWtMinbsFXw07uwjqJIpuxFY+1p9L+ZchE6AJidd6U1aZG4HRzapxVrC2qBt'
                 '/Ea1OmogCY1yf8KAqZezD1nWph530rCgZJj9DhIOLNVHjZ7y9asm5TqB4qvselui9YRbtP6oy0NPNaOh6tCskBJEapWeRg'
                 'bfmTTCpXbPk9LhxAwTZzBl1vENAUyjjycA06mfugrjmpfyScfxv6sWaWdYbGbJo+f5wbhOrrl4vGbE4pO73EAFbfBA8ask'
                 'GkdW9F4fVekFLAKcLJrV9rruVfDbiO3iqkkLTzfRD8QZIXt14KXMa8Wv1u6a1L5Plxv5zRtnjXMg0Cepzesm4csaSdi6dQ'
                 'Qtp/pYA7ve1AngX2DQpnisF+PdABLIrl6dlEdD+idQ5cncnwJng51RUqMLA4/U3MdFD100MQuG4LYrgoVi/JHHvlkDZPBY'
                 'WiwXMZ1iba7BN/iKo3pF4tBbddOJl9TO7oJrYu+GI9LH7+LRLiO6EkV3fZlekVYkPPhQlGtyXPnFBSqvOBf7ofo+c8xFEm'
                 '1hbFtwaGOk97rz2U802X9GcEGK+ARW+NKrWZwIkpo+EG52k1GgQddzvD8im9TQyj78YcJ2ZiExPvuCT2eMWh4trk8lm+lE'
                 '0LfNHdjwn3MC0htyvsnzRAsbYiogXcn0ezedbYD7fZZ+r0O2aqdppaTsWq7Ev/T0DE1aPdnYJA+tvi54z1FBQqquhcNsDZ'
                 'WuQ1eMQsrTLLKX0XizNJWK1FkxO6Ig28aivUAUilxp+Py6JOPpkjza8z2MRn9tUqvLuOxdS8iLhmvYahvlxkQ3oDB1m5Q4'
                 'd2sFKzMa8Y8h9XY7LKGxlrjlmA4SrmyTTeWE6Q1SzOQ8lYtAfbKrNP4kZFpfY=212FD3x19z9sWBHDJACbC00B75E')

REFRESH_TOKEN = 'eOhX6bz9AjyKiWNiJQecRmCGKby5/RcaP6oWtMinbsFXw07uwjqJIpuxFY+1p9L+ZchE6AJidd6U1aZG4HRzapxVrC2qBt/Ea1OmogCY1yf8KAqZezD1nWph530rCgZJj9DhIOLNVHjZ7y9asm5TqB4qvselui9YRbtP6oy0NPNaOh6tCskBJEapWeRgbfmTTCpXbPk9LhxAwTZzBl1vENAUyjjycA06mfugrjmpfyScfxv6sWaWdYbGbJo+f5wbhOrrl4vGbE4pO73EAFbfBA8askGkdW9F4fVekFLAKcLJrV9rruVfDbiO3iqkkLTzfRD8QZIXt14KXMa8Wv1u6a1L5Plxv5zRtnjXMg0Cepzesm4csaSdi6dQQtp/pYA7ve1AngX2DQpnisF+PdABLIrl6dlEdD+idQ5cncnwJng51RUqMLA4/U3MdFD100MQuG4LYrgoVi/JHHvlkDZPBYWiwXMZ1iba7BN/iKo3pF4tBbddOJl9TO7oJrYu+GI9LH7+LRLiO6EkV3fZlekVYkPPhQlGtyXPnFBSqvOBf7ofo+c8xFEm1hbFtwaGOk97rz2U802X9GcEGK+ARW+NKrWZwIkpo+EG52k1GgQddzvD8im9TQyj78YcJ2ZiExPvuCT2eMWh4trk8lm+lE0LfNHdjwn3MC0htyvsnzRAsbYiogXcn0ezedbYD7fZZ+r0O2aqdppaTsWq7Ev/T0DE1aPdnYJA+tvi54z1FBQqquhcNsDZWuQ1eMQsrTLLKX0XizNJWK1FkxO6Ig28aivUAUilxp+Py6JOPpkjza8z2MRn9tUqvLuOxdS8iLhmvYahvlxkQ3oDB1m5Q4d2sFKzMa8Y8h9XY7LKGxlrjlmA4SrmyTTeWE6Q1SzOQ8lYtAfbKrNP4kZFpfY=212FD3x19z9sWBHDJACbC00B75E'

api_data = {'grant_type': 'refresh_token',
            'refresh_token': REFRESH_TOKEN,
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI
            }


def get_token():
    token = json.loads(requests.post('https://api.tdameritrade.com/v1/oauth2/token', data=api_data).text)
    token = f'{token["token_type"]} {token["access_token"]}'
    return token


TOKEN = get_token()


class Stock:
    def __init__(self, symbol, fair_value, end_days=65):
        self.account_id = ACCOUNT_ID
        self.base_url = 'https://api.tdameritrade.com/v1/marketdata/'
        self.symbol = symbol.upper()
        self.fair_value = fair_value
        self._get_basic_data()
        today = dt.date.today()
        end = today + dt.timedelta(days=end_days)
        start_date = today.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')
        self.puts, self.calls = self._get_option_chain(start_date, end_date, strike_range='OTM')
        self.normal_dist = self._get_standard_deviation()

    def _get_basic_data(self):
        time.sleep(.3)
        headers = {"Authorization": TOKEN}
        path_param = f'{self.symbol}/quotes'
        resp = json.loads(requests.get(self.base_url + path_param, headers=headers).text)
        try:
            self.price = float(resp[self.symbol]['lastPrice'])
            self.dividend = float(resp[self.symbol]['divAmount'])
            self.dividend_yield = float(resp[self.symbol]['divYield'])
        except KeyError:
            print(f'{self.symbol} - KeyError - {resp}')

    def _get_standard_deviation(self, period_type='year', periods='1'):
        time.sleep(.3)
        headers = {"Authorization": TOKEN}
        path_params = (f'{self.symbol}/pricehistory?'
                       f'periodType={period_type}&'
                       f'period={periods}&'
                       f'frequencyType=monthly')
        resp = json.loads(requests.get(self.base_url + path_params, headers=headers).text)
        try:
            nd = NormalDist.from_samples([(x['close'] - x['open']) / x['open'] for x in resp['candles']])
            return nd
        except TypeError:
            print(f'{self.symbol} - TypeError')
            pass
        except KeyError:
            print(f'{self.symbol} - KeyError')
            pass
        except StatisticsError:
            print(f'{self.symbol} - StatisticsError')
            pass

    def _get_option_chain(self, start_date, end_date,
                          contract_type='ALL', strike_range='ALL',
                          option_type='S'):
        time.sleep(.3)
        headers = {"Authorization": TOKEN}
        path_params = (f'chains?'
                       f'symbol={self.symbol}&'
                       f'contractType={contract_type}&'
                       f'range={strike_range}&'
                       f'fromDate={start_date}&'
                       f'optionType={option_type}&'
                       f'toDate={end_date}')
        resp = json.loads(requests.get(self.base_url + path_params, headers=headers).text)
        puts = resp.get('putExpDateMap')
        calls = resp.get('callExpDateMap')
        return puts, calls


def place_order(symbol1, symbol2, price):
    headers = {"Authorization": TOKEN,
               "Content-type": "Application/json"}
    base_url = 'https://api.tdameritrade.com/v1/accounts/'
    path_param = f'{ACCOUNT_ID}/orders'
    data = {"orderType": "NET_CREDIT",
            "session": "NORMAL",
            "price": f"{price}",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "BUY_TO_OPEN",
                    "quantity": 1,
                    "instrument": {
                        "symbol": f"{symbol1}",
                        "assetType": "OPTION"
                    }
                },
                {
                    "instruction": "SELL_TO_OPEN",
                    "quantity": 1,
                    "instrument": {
                        "symbol": f"{symbol2}",
                        "assetType": "OPTION"
                    }
                }
            ]
            }
    resp = requests.post(base_url + path_param, headers=headers, data=json.dumps(data))
    return resp


class Option:
    def __init__(self, option):
        self.ask = float(option['ask'])
        self.ask_size = float(option['askSize'])
        self.bid = float(option['bid'])
        self.bid_size = float(option['bidSize'])
        self.daysToExpiration = int(option['daysToExpiration'])
        self.delta = float(option['delta'])
        self.gamma = float(option['gamma'])
        self.last = float(option['last'])
        self.mark = float(option['mark'])
        self.open_interest = float(option['openInterest'])
        self.strikePrice = float(option['strikePrice'])
        self.symbol = option['symbol']
        self.theta = float(option['theta'])
        self.total_volume = float(option['totalVolume'])
        self.vega = float(option['vega'])
        self.volatility = float(option['volatility'])

    def __iter__(self):
        for x, y in self.__dict__.items():
            yield x, y


def update(stock, value):
    stock = Stock(stock, value)
    today = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d')
    current_hour = dt.datetime.now().hour
    if value > 0:
        all_options = stock.puts.items()
        nd = stock.normal_dist.quantiles(8)[0]
    else:
        all_options = stock.calls.items()
        nd = stock.normal_dist.quantiles(10)[8]

    cagr_mapping = {range(0, 8): 9, range(8, 15): 16, range(15, 22): 23, range(22, 29): 30, range(29, 36): 37}
    for exp_date, chain in all_options:
        days = int(exp_date.split(':')[1])
        cagr_days = next((cagr_mapping[d] for d in cagr_mapping if days in d), days)

        # Minimum bar to pass don't clog DB with unsellable options
        try:
            options = [Option(o[0]) for strike, o in chain.items() if (.75 < float(strike) / stock.price < 1.25 and
                                                                       (o[0]['ask'] - o[0]['bid']) / stock.price < .015 and
                                                                       o[0]['bid'] > .1 and
                                                                       o[0]['openInterest'] >= 1
                                                                       )]
        except AttributeError:
            logger.warning(f'{o[0]["symbol"]} error')
            continue

        for option in options:
            symbol = option.symbol
            strike_percent = round((option.strikePrice / stock.price), 2)
            profit_percent = round((option.mark / option.strikePrice / .15), 3)
            cdf = round(stock.normal_dist.cdf(strike_percent - 1), 3)
            pdf = round(stock.normal_dist.pdf(strike_percent - 1), 3)
            stddev = round(stock.normal_dist.stdev, 3)
            cagr = round(((1 + profit_percent) ** (1 / (cagr_days / 365))) - 1, 2)
            try:
                stock_symbol = StockSymbol.objects.get(symbol=symbol.split('_')[0])
            except ObjectDoesNotExist:
                symbol = symbol.split('_')[0]
                symbol = f'{symbol[:-1]}.{symbol[-1]}'
                stock_symbol = StockSymbol.objects.get(symbol=symbol)
            o = dict(symbol=symbol,
                     ticker=stock_symbol,
                     sell=option.mark,
                     stddev=stddev,
                     cdf=cdf,
                     pdf=pdf,
                     strike_discount=strike_percent,
                     profit_percent=profit_percent,
                     cagr=cagr,
                     days_to_exp=days,
                     expired=False,
                     strike=option.strikePrice,
                     nd=nd)
            o, created = screen(stock, o)
            if created:
                continue
            if o['days_to_exp'] % 7 == 0:
                ModelOption.objects.get_or_create(symbol=o['symbol'], date=today, defaults=o)
                logger.debug(f'Added {o["symbol"]}')
            if o['days_to_exp'] == 0 and current_hour >= 15:
                expired = ModelOption.objects.filter(symbol=o['symbol'])
                expired.update(expired=True)
                if option.mark < .05:
                    expired.update(buy=0)
                else:
                    expired.update(buy=option.mark)


def screen(s, o):
    nd = o.pop('nd')
    required_strike = s.price + (s.price * (sqrt(o['days_to_exp'] / 30) * nd))
    today = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d')

    strike = o.pop('strike')
    if (s.fair_value > 0 and
            o['strike_discount'] <= .95 and
            strike < required_strike and
            o['cagr'] > 2.5 and
            1 <= o['days_to_exp'] <= 35):
        o['screened'] = True
    if (s.fair_value == 0 and
            1.07 <= o['strike_discount'] < 2 and
            strike > required_strike and
            o['cagr'] > 2.5 and
            1 <= o['days_to_exp'] < 30):
        o['screened'] = True

    if o.get('screened'):
        _, created = ModelOption.objects.update_or_create(symbol=o['symbol'], date=today, defaults=o)
        logger.info(f'symbol={o["symbol"]}, sell={o["sell"]} strike_discount={o["strike_discount"]}, '
                    f'profit_percent={o["profit_percent"]}, days_to_exp={o["days_to_exp"]} - {o["cagr"]}')
    else:
        created = False

    return o, created


def option_screen(good_stocks, bad_stocks):
    for stock in good_stocks:
        update(stock.symbol, stock.fair_value)
    for stock in bad_stocks:
        update(stock.symbol, 0)
