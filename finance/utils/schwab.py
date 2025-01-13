import base64
import datetime
import json
import logging
from math import sqrt
from statistics import NormalDist, StatisticsError

import django

django.setup()
import requests

from finance.models import StockSymbol

logger = logging.getLogger(__name__)

REFRESH_TOKEN = ('o9zhgVMj-OQlErL_SHl0Ha-74nlE7zhHN9q10B9JedWw83ONP2PZMyMdpMEQQabXbFBXrM'
                 'U59CU7LVYQ5NB9jCKm5WjwdvF_119sGOfnSrI_PKMAcyNDtHzGW3DdbRueiiWM8ZKVe2U@')


class Token:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '_' + name
        self.date = '_' + name + '_date'

    def __get__(self, obj, cls):
        if hasattr(obj, self.date):
            now = datetime.datetime.now()
            expires = getattr(obj, self.date)
            if now < expires:
                return getattr(obj, self.private_name)
            else:
                setattr(obj, self.private_name, self.set_token(obj))
                return getattr(obj, self.private_name)
        else:
            setattr(obj, self.private_name, self.set_token(obj))
            return getattr(obj, self.private_name)

    def set_token(self, obj):
        now = datetime.datetime.now()
        auth = getattr(obj, 'auth')
        token_url = getattr(obj, 'token_url')
        data = {"grant_type": "refresh_token",
                'refresh_token': REFRESH_TOKEN
                }
        headers = {'Authorization': f'Basic {auth}',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.post(token_url, data=data, headers=headers)
        resp = json.loads(resp.text)
        access_token = resp['access_token']
        ttl = resp['expires_in']
        expires_in = now + datetime.timedelta(seconds=ttl - 50)
        setattr(obj, self.date, expires_in)
        return access_token


class SchwabAPI:
    access_token = Token()

    def __init__(self):
        self.base_url = 'https://api.schwabapi.com/v1'
        self.data_url = 'https://api.schwabapi.com/marketdata/v1'
        self.app_key = 'a8GcVDUK3YTIBqccTGyEYRxy7iRDriYq'
        self.app_secret = '5rG9eG2ixlreEYNN'
        self.auth = base64.b64encode(f'{self.app_key}:{self.app_secret}'.encode()).decode()
        self.callback_url = 'https://127.0.0.1'
        self.refresh_token = REFRESH_TOKEN
        auth_url_params = f'client_id={self.app_key}&redirect_uri={self.callback_url}'
        self.auth_url = f'{self.base_url}/oauth/authorize?{auth_url_params}'
        self.token_url = f'{self.base_url}/oauth/token'
        # logger.info(self.access_token)

    def quote(self, ticker):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        path_param = f'{ticker}/quotes'
        try:
            resp = json.loads(requests.get(f'{self.data_url}/{path_param}', headers=headers).text)
            price = float(resp[ticker]['quote']['lastPrice'])
            dividend = float(resp[ticker]['fundamental']['divAmount'])
            dividend_yield = float(resp[ticker]['fundamental']['divYield'])
            return price, dividend, dividend_yield
        except KeyError:
            logger.error(f'KeyError: {ticker}')
            return None

    def price_history(self, ticker):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        path_params = (f'pricehistory?symbol={ticker}&'
                       f'periodType=year&'
                       f'period=1&'
                       f'frequencyType=monthly')
        try:
            resp = json.loads(requests.get(f'{self.data_url}/{path_params}', headers=headers).text)
        except json.JSONDecodeError:
            logger.error(f'{ticker} - Could not read {self.data_url}/{path_params}')
        try:
            nd = NormalDist.from_samples([(x['close'] - x['open']) / x['open'] for x in resp['candles']])
            return nd
        except TypeError:
            logger.error(f'{ticker} - TypeError')
            pass
        except KeyError:
            logger.error(f'{ticker} - KeyError')
            pass
        except StatisticsError:
            logger.error(f'{ticker} - StatisticsError')
            pass

    def chains(self, ticker, start_date, end_date):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        path_params = (f'chains?'
                       f'symbol={ticker}&'
                       f'contractType=ALL&'
                       f'range=OTM&'
                       f'fromDate={start_date}&'
                       f'optionType=S&'
                       f'toDate={end_date}')
        resp = json.loads(requests.get(f'{self.data_url}/{path_params}', headers=headers).text)
        puts = resp.get('putExpDateMap')
        calls = resp.get('callExpDateMap')
        return puts, calls


class Stock:
    def __init__(self, ticker, fair_value=0, end_days=65):
        today = datetime.date.today()
        end = today + datetime.timedelta(days=end_days)
        start_date = today.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')
        self.ticker = ticker.upper()
        self.fair_value = fair_value
        self.price, self.dividend, self.dividend_yield = schwab.quote(self.ticker)
        self.normal_dist = schwab.price_history(self.ticker)
        self.puts, self.calls = schwab.chains(self.ticker, start_date, end_date)


class Option:
    def __init__(self, option):
        self.ask = float(option['ask'])
        self.ask_size = float(option['askSize'])
        self.bid = float(option['bid'])
        self.bid_size = float(option['bidSize'])
        self.last = float(option['last'])
        self.mark = float(option['mark'])
        self.daysToExpiration = int(option['daysToExpiration'])
        self.open_interest = float(option['openInterest'])
        self.strikePrice = float(option['strikePrice'])
        self.symbol = option['symbol']
        self.total_volume = float(option['totalVolume'])
        self.volatility = float(option['volatility'])
        self.delta = float(option['delta'])
        self.gamma = float(option['gamma'])
        self.theta = float(option['theta'])
        self.vega = float(option['vega'])

    def __iter__(self):
        for x, y in self.__dict__.items():
            yield x, y


class Screen:
    def __call__(self, stock):
        if stock.stars >= 4:
            stock = Stock(stock.symbol, fair_value=stock.fair_value)
            chain = stock.puts
        else:
            stock = Stock(stock.symbol, fair_value=0)
            chain = stock.calls
        options = self.trash_filter(chain, stock)
        if not options:
            return
        data = self.assign_data(options, stock)
        if data and stock.fair_value:
            self.put_screen(data)
        else:
            self.call_screen(data)

    @staticmethod
    def trash_filter(chain, stock):
        # Minimum bar to pass don't clog DB with unsellable options
        options = []
        # Chain is {"date": {"strike": [option1, option2]}}
        try:
            for _, strikes in chain.items():
                for strike, o in strikes.items():
                    o = o[0]
                    if (.7 < float(strike) / stock.price < 1.35 and
                            (o['ask'] - o['bid']) / stock.price < .015 and
                            o['bid'] > .1 and
                            o['ask'] > .1 and
                            o['openInterest'] >= 1):
                        options.append(Option(o))
        except AttributeError:
            logger.error(stock)
            logger.error(f'{stock.ticker} - Attribute Error')
            return []
        return options

    def assign_data(self, options, stock):
        data = []
        for option in options:
            if option.daysToExpiration == 0:
                days = 1
            else:
                days = option.daysToExpiration
            try:
                stock_symbol = StockSymbol.objects.get(symbol=stock.ticker)
                strike_discount = round((option.strikePrice / stock.price), 2)
                # profit_percent = round((option.mark / option.strikePrice / .15), 3)
                profit_percent = round((option.mark * 100) / self.trade_requirement(option, stock.price), 3)
                cdf = round(stock.normal_dist.cdf(sqrt(30 / days) * (strike_discount - 1)), 3)
                pdf = round(stock.normal_dist.pdf(sqrt(30 / days) * (strike_discount - 1)), 3)
                stddev = round(stock.normal_dist.stdev, 3)
                cagr = self.calc_cagr(profit_percent, days)
            except AttributeError:
                logger.error(f'Unable to screen {stock_symbol}')
                return []
            data.append({'ticker': stock_symbol,
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
                         })
        return data

    @staticmethod
    def put_screen(data):
        filtered_options = []
        for item in data:
            days = item.pop('calculation_days')
            nd = item.pop('nd').quantiles(8)[0]
            current_price = item.pop('current_price')
            required_strike = current_price + (current_price * (sqrt(days / 30) * nd))
            strike_price = item.pop('strike_price')
            space = item["symbol"].find(' ')
            symbol = item["symbol"][:space]
            date = item["symbol"][8:12]

            if (item['strike_discount'] <= .92 and
                    strike_price < required_strike and
                    item['cagr'] > 2 and
                    5 <= item['days_to_exp'] <= 35):
                item['screened'] = True
                filtered_options.append(item)
                print(f'{symbol} -  put - {date} - {strike_price} - {item["cagr"]}')
        return filtered_options

    @staticmethod
    def call_screen(data):
        filtered_options = []
        for item in data:
            days = item.pop('calculation_days')
            nd = item.pop('nd').quantiles(8)[6]
            current_price = item.pop('current_price')
            required_strike = current_price + (current_price * (sqrt(days / 30) * nd))
            strike_price = item.pop('strike_price')

            if (1.08 <= item['strike_discount'] and
                    strike_price > required_strike and
                    item['cagr'] > 2.75 and
                    1 <= item['days_to_exp'] < 21):
                item['screened'] = True
                filtered_options.append(item)
        return filtered_options

    @staticmethod
    def calc_cagr(rate, days):
        cagr_mapping = {range(0, 8): 9, range(8, 15): 16, range(15, 22): 23, range(22, 29): 30, range(29, 36): 37}
        cagr_days = next((cagr_mapping[d] for d in cagr_mapping if days in d), days)
        return round(((1 + rate) ** (1 / (cagr_days / 365))) - 1, 2)

    @staticmethod
    def trade_requirement(option, price):
        option1 = ((.2 * price * 100) + ((option.strikePrice - price) * 100) + option.mark * 100)
        option2 = (.1 * option.strikePrice * 100) + option.mark * 100
        return max(option1, option2)


schwab = SchwabAPI()


def option_screen(stocks):
    for stock in stocks:
        print(stock)
        if "." not in stock.symbol:
            Screen()(stock)


def option_update():
    pass


if __name__ == '__main__':
    schwab = SchwabAPI()
    # This will launch in browser, auth in and copy the code from the URL, and add a @ after
    print(schwab.auth_url)
    print('Print code')
    code = input() + "@"

    payload = {'grant_type': 'authorization_code',
               'redirect_uri': schwab.callback_url,
               'code': code
               }
    auth_headers = {'Authorization': f'Basic {schwab.auth}',
                    'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(schwab.token_url, data=payload, headers=auth_headers)
    tokens = json.loads(response.text)
    refresh_token = tokens['refresh_token']
    print(refresh_token)
