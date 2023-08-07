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
REFRESH_TOKEN = ('HhatTzq1ZH0epCwOGQs5ceOGYsdI6aAyWhVeaRR06HsHw91VtLpDirUGqdTgaSqR6eQbCeozdIaigv0r'
                 '7hpc6zK/PTbpZStkiCtdLTVZlpVu9v6elFLDXEgPDC+xESw0cxwNTeeT3VTkHfV7KWtZJH1fc99kch7P'
                 'ixon+Z8PXR9ZBFAlxOBd+TzHd2Djg7YeI3TNQoZSsI8Yn75LxAL0wkVoSFomIMo7niYpDfRyfmMQqr+p'
                 'QA7oHDK+G/m2w68+QogbarKOaCfNBxk1fPDw6/o8V6gYapIYzAtVMdvGQURJe9+t1sM8WnUcrHbtqK5M'
                 'l7ekCCZvhCftWn6B0PmwhDavMpo6uNI2u0TKzgrwwtdFPEXssVFx4JYpHxGLu5ERCUc0KCMkGIcIWUrq'
                 'F2yi1GRpakP7RqRuEgP+BNWeoDbF+nZ2nrHX+kG1u84100MQuG4LYrgoVi/JHHvllFPTTaniXjIfJD3f'
                 'hp8iIZyeJn7b3qr4AvxDwDEbGkRFHEKLttCyp/liMIP9BP0llXRvvX8kC7VRH2xpq6bPWocMB/Kn7j/s'
                 'c6q3xcmhNoIQWX3lseOQOJwa4ohgNgg+aSsr/i6X/v6tZdthhZXromhfxJctgVSMRTC5K9BZBrGRzgQo'
                 '5f/2FrTGFFoktXbA8vpNyn2BV2JHS/16iOCpWKv7Wd4tzx5bKZ+/4LgG/M+udySZDXcdXPMr7MYFTAY7'
                 'PxyI4jmnPxUGyL+9WU+k9pi1iMKUPU6NglPl1wDJkhffP8bD2UdnMqoQW9jTAN/8WJnqso9X7hrbG2WN'
                 'NTB16zjeLUv0Jnnz9O8IPEz/C0zBWI4mzQo2+Vmb29YHrME3SBgb7l0w89Anf6FLFpZZbLhgNOnGfc+m'
                 'dkUzrEon9qYfjOb879cf7EZDe2M=212FD3x19z9sWBHDJACbC00B75E')

api_data = {'grant_type': 'refresh_token',
            'refresh_token': REFRESH_TOKEN,
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI
            }


def get_token():
    token = json.loads(requests.post('https://api.tdameritrade.com/v1/oauth2/token', data=api_data).text)
    token = f'{token["token_type"]} {token["access_token"]}'
    return token

class Token:
    def __get__(self, instance, owner):
        pass
    def __set__(self, instance, value):
        pass

class Stock:
    token = get_token()

    @classmethod
    def reset_token(cls):
        cls.token = get_token()

    def __init__(self, symbol, fair_value, end_days=65):
        time.sleep(.15)
        self.account_id = ACCOUNT_ID
        self.base_url = 'https://api.tdameritrade.com/v1/marketdata/'
        self.symbol = symbol.upper()
        self.fair_value = fair_value
        today = dt.date.today()
        end = today + dt.timedelta(days=end_days)
        start_date = today.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')
        self._get_basic_data()
        self.puts, self.calls = self._get_option_chain(start_date, end_date, strike_range='OTM')
        self.normal_dist = self._get_standard_deviation()

    def _get_basic_data(self):
        time.sleep(.15)
        headers = {"Authorization": self.token}
        path_param = f'{self.symbol}/quotes'
        try:
            resp = json.loads(requests.get(self.base_url + path_param, headers=headers).text)
            self.price = float(resp[self.symbol]['lastPrice'])
            self.dividend = float(resp[self.symbol]['divAmount'])
            self.dividend_yield = float(resp[self.symbol]['divYield'])
        except KeyError:
            # self.reset_token()
            try:
                self._get_basic_data()
            except RecursionError:
                logger.error(f'{self.symbol} - KeyError - {resp}')

    def _get_standard_deviation(self, period_type='year', periods='1'):
        time.sleep(.15)
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
            logger.error(f'{self.symbol} - TypeError')
            pass
        except KeyError:
            logger.error(f'{self.symbol} - KeyError')
            pass
        except StatisticsError:
            logger.error(f'{self.symbol} - StatisticsError')
            pass

    def _get_option_chain(self, start_date, end_date,
                          contract_type='ALL', strike_range='ALL',
                          option_type='S'):
        time.sleep(.15)
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
    headers = {"Authorization": get_token(),
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
    try:
        if value > 0:
            all_options = stock.puts.items()
        else:
            all_options = stock.calls.items()
    except AttributeError:
        logger.error(f'{stock.symbol} no option chain')
        return

    for exp_date, chain in all_options:
        options = initial_filter(chain, stock)
        for option in options:
            data = screen_data(option, stock)
            if data:
                if value > 0:
                    data = put_screen(data)
                else:
                    data = call_screen(data)
            else:
                continue
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
    options = []
    try:
        for strike, o in chain.items():
            if (.7 < float(strike) / stock.price < 1.35 and
                    (o[0]['ask'] - o[0]['bid']) / stock.price < .014 and
                    o[0]['bid'] > .1 and
                    o[0]['ask'] > .1 and
                    o[0]['openInterest'] >= 1):
                options.append(Option(o[0]))
    except AttributeError:
        logger.error(f'{stock.symbol} - Attribute Error')
        return []
    return options


def screen_data(option, stock):
    if option.daysToExpiration == 0:
        days = 1
    else:
        days = option.daysToExpiration
    try:
        stock_symbol = StockSymbol.objects.get(symbol=stock.symbol)
        strike_discount = round((option.strikePrice / stock.price), 2)
        profit_percent = round((option.mark / option.strikePrice / .15), 3)
        cdf = round(stock.normal_dist.cdf(sqrt(30 / days) * (strike_discount - 1)), 3)
        pdf = round(stock.normal_dist.pdf(sqrt(30 / days) * (strike_discount - 1)), 3)
        stddev = round(stock.normal_dist.stdev, 3)
        cagr = calc_cagr(profit_percent, days)
    except AttributeError:
        logger.error(f'Unable to screen {stock_symbol}')
        return
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
            'calculation_days': days,
            'sold': 0
            }


def put_screen(data):
    days = data.pop('calculation_days')
    nd = data.pop('nd').quantiles(8)[0]
    current_price = data.pop('current_price')
    required_strike = current_price + (current_price * (sqrt(days / 30) * nd))
    strike_price = data.pop('strike_price')

    if (data['strike_discount'] <= .92 and
            strike_price < required_strike and
            data['cagr'] > 2.25 and
            5 <= data['days_to_exp'] <= 35):
        data['screened'] = True
    return data


def call_screen(data):
    days = data.pop('calculation_days')
    nd = data.pop('nd').quantiles(8)[6]
    current_price = data.pop('current_price')
    required_strike = current_price + (current_price * (sqrt(days / 30) * nd))
    strike_price = data.pop('strike_price')

    if (1.08 <= data['strike_discount'] and
            strike_price > required_strike and
            data['cagr'] > 2.75 and
            1 <= data['days_to_exp'] < 21):
        data['screened'] = True
    return data


def option_screen(good_stocks, bad_stocks):
    for stock in good_stocks:
        print(stock)
        screen(stock.symbol, stock.fair_value)
    for stock in bad_stocks:
        print(stock)
        screen(stock.symbol, 0)


def option_update():
    today = dt.datetime.strftime(dt.datetime.now(), '%m%d%y')
    options = ModelOption.objects.filter(expired=False, symbol__contains=today).order_by('symbol')
    symbol = ''
    bulk_options = []
    for option in options:
        option.expired = True
        if option.ticker.symbol != symbol:
            symbol = option.ticker.symbol
            stock = Stock(symbol, 0)
        # DTS = DateTypeStrike
        dts = option.symbol.split('_')[1]
        try:
            if 'C' in dts:
                strike = float(dts.split('C')[1])
                if stock.price > strike:
                    option.buy = round(stock.price - strike, 2)
                else:
                    option.buy = 0.0
                bulk_options.append(option)
            elif 'P' in dts:
                strike = float(dts.split('P')[1])
                if stock.price > strike:
                    option.buy = 0.0
                else:
                    option.buy = round(strike - stock.price, 2)
                bulk_options.append(option)
        except AttributeError:
            logger.error("Attribute Error")
        ModelOption.objects.bulk_update(bulk_options, ['expired', 'buy'], batch_size=100)
        bulk_options.clear()
