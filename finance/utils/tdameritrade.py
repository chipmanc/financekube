import datetime as dt
import json
import logging
from math import sqrt
from statistics import NormalDist, StatisticsError
import time

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
REFRESH_TOKEN = 'qe78H73fVUr0TAdBpJHRoAAzKEDAteF3W4p3MC5DqVKpJ9ywfajF8pIXNZSok30OraOi/atdDKmuvr48pa6/mk8rqPnp5aSzhoxLpZx3vJKr+fNia4LWwSSDaOPo8Bp/Q2FK9lQN2krWWSPqf7FTqFwOHKqkCkU/jvd6UM95GpA8R6AT6h1saiU1K9hXAn40+qbXI9UdlyFSKwDF3/DlfOZZ+BTkPT8IUw+RjH3zRWA1KIFqR7Nql9uoAOVFjq4ZLKA8141i2IvNvogipbfI5vg4nGY+g2pRft1Ke06WuAg65tTq3fcQ/C+EAdWNvthVXZTFdtP1MZ2woWRA7O2gK9Y9ZuxfENq6VhCqK8k/JB7qF2fyVfj4+DKhpBfzHfwSb3VVwKx+AokDbmwCDSZazkxAr3ZYftbK7KzKObvVhGqwJGAoXjfgEF8p07K100MQuG4LYrgoVi/JHHvlpHSPKuvGMZGhiKRm7z+SAlEblkyLp7A4u3Bu2/wVTGABSILC6WgYd85jP1CQwPKFDNeMAcp5xYWc/a6Me1Efv+wUg8PJHQviqQP/UweYic0zYIdDKkJVtqOzG7srKs4QFSLR/NFkUClT/GQ8lqzwdeinU4vaZcbnW/DCOtgWaOeg6TtHq6Zag5vHBB1KeKmy2o40RlGljwtuK+spKKW8tDPV3gTYQdWQoz4dho2RqyKWmTnXrSUgvOwwbGiliotXQQ7l629r35N0hU5qjubhOV56nvVI+W8ieQfW4GNrl+zYNSYY7COzUHO56C5XqDYS4a8KzCE5wa+ax8kIwhSn/jl5iogAC6QUFbn/mXcgdAy1+2d3KYZj9vTxG2bXYgHFI30W7w1+skUNTKTGzDLdGo09GB5HQDAD4kWEoMH/OSkDRwDBgZ6/A+7FZnU=212FD3x19z9sWBHDJACbC00B75E'

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
        time.sleep(.12)
        print(symbol)
        self.token = get_token()
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
        time.sleep(.11)
        headers = {"Authorization": self.token}
        path_param = f'{self.symbol}/quotes'
        resp = json.loads(requests.get(self.base_url + path_param, headers=headers).text)
        try:
            self.price = float(resp[self.symbol]['lastPrice'])
            self.dividend = float(resp[self.symbol]['divAmount'])
            self.dividend_yield = float(resp[self.symbol]['divYield'])
        except KeyError:
            print(f'{self.symbol} - KeyError - {resp}')

    def _get_standard_deviation(self, period_type='year', periods='1'):
        time.sleep(.11)
        headers = {"Authorization": self.token}
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
        time.sleep(.11)
        headers = {"Authorization": self.token}
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


def screen(stock, value):
    stock = Stock(stock, value)
    if value > 0:
        all_options = stock.puts.items()
    else:
        all_options = stock.calls.items()

    for exp_date, chain in all_options:
        options = initial_filter(chain, stock)
        for option in options:
            data = screen_data(option, stock)
            if value > 0:
                data = put_screen(data)
            else:
                data = call_screen(data)
            update_db(data)


def update_db(data):
    today = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d')
    if data.get('screened'):
        ModelOption.objects.update_or_create(symbol=data['symbol'], date=today, defaults=data)
        logger.info(f'symbol={data["symbol"]}, sell={data["sell"]} strike_discount={data["strike_discount"]}, '
                    f'days_to_exp={data["days_to_exp"]}, cagr={data["cagr"]}')
        return
    if data.get('days_to_exp') % 7 == 0:
        ModelOption.objects.get_or_create(symbol=data['symbol'], date=today, defaults=data)
        logger.debug(f'Added {data["symbol"]}')
        return


def calc_cagr(rate, days):
    cagr_mapping = {range(0, 8): 9, range(8, 15): 16, range(15, 22): 23, range(22, 29): 30, range(29, 36): 37}
    cagr_days = next((cagr_mapping[d] for d in cagr_mapping if days in d), days)
    return round(((1 + rate) ** (1 / (cagr_days / 365))) - 1, 2)


def initial_filter(chain, stock):
    # Minimum bar to pass don't clog DB with unsellable options
    try:
        options = (Option(o[0]) for strike, o in chain.items() if (.7 < float(strike) / stock.price < 1.3 and
                                                                   (o[0]['ask'] - o[0]['bid']) / stock.price < .015 and
                                                                   o[0]['bid'] > .1 and
                                                                   o[0]['openInterest'] >= 1
                                                                   ))
    except AttributeError:
        logger.warning(f'{stock.symbol} error')
        return []
    return options


def screen_data(option, stock):
    if option.daysToExpiration == 0:
        days = 1
    else:
        days = option.daysToExpiration
    stock_symbol = StockSymbol.objects.get(symbol=stock.symbol)
    strike_discount = round((option.strikePrice / stock.price), 2)
    profit_percent = round((option.mark / option.strikePrice / .15), 3)
    cdf = round(stock.normal_dist.cdf(sqrt(30 / days) * (strike_discount - 1)), 3)
    pdf = round(stock.normal_dist.pdf(sqrt(30 / days) * (strike_discount - 1)), 3)
    stddev = round(stock.normal_dist.stdev, 3)
    cagr = calc_cagr(profit_percent, days)
    return {'ticker': stock_symbol,
            'symbol': option.symbol,
            'strike_discount': strike_discount,
            'profit_percent': profit_percent,
            'cdf': cdf,
            'pdf': pdf,
            'stddev': stddev,
            'cagr': cagr,
            'sell': option.mark,
            'days_to_exp': option.daysToExpiration,
            'strike_price': option.strikePrice,
            'nd': stock.normal_dist,
            'current_price': stock.price,
            'calculation_days': days
            }


def put_screen(data):
    days = data.pop('calculation_days')
    nd = data.pop('nd').quantiles(8)[0]
    current_price = data.pop('current_price')
    required_strike = current_price + (current_price * (sqrt(days / 30) * nd))
    strike_price = data.pop('strike_price')

    if (data['strike_discount'] <= .92 and
            strike_price < required_strike and
            data['cagr'] > 2.5 and
            1 <= data['days_to_exp'] <= 35):
        data['screened'] = True
    return data


def call_screen(data):
    days = data.pop('calculation_days')
    nd = data.pop('nd').quantiles(9)[7]
    current_price = data.pop('current_price')
    required_strike = current_price + (current_price * (sqrt(days / 30) * nd))
    strike_price = data.pop('strike_price')

    if (1.08 <= data['strike_discount'] < 2 and
            strike_price > required_strike and
            data['cagr'] > 3 and
            1 <= data['days_to_exp'] < 25):
        data['screened'] = True
    return data


def option_screen(good_stocks, bad_stocks):
    for stock in good_stocks:
        screen(stock.symbol, stock.fair_value)
    for stock in bad_stocks:
        screen(stock.symbol, 0)


def option_update():
    today = dt.datetime.strftime(dt.datetime.now(), '%m%d%y')
    options = ModelOption.objects.filter(expired=False, symbol__contains=today).order_by('symbol')
    symbol = ''
    for option in options:
        if option.ticker.symbol != symbol:
            symbol = option.ticker.symbol
            stock = Stock(symbol, 0)
        dts = option.symbol.split('_')[1]
        if 'C' in dts:
            strike = float(dts.split('C')[1])
            if stock.price > strike:
                mark = round(stock.price - strike, 2)
            else:
                mark = 0.0
        elif 'P' in dts:
            strike = float(dts.split('P')[1])
            if stock.price > strike:
                mark = 0.0
            else:
                mark = round(strike - stock.price, 2)
        ModelOption.objects.filter(symbol=option.symbol).update(expired=True, buy=mark)
