from datetime import date, timedelta
import logging
import os
import time

from django.core.exceptions import FieldError, ObjectDoesNotExist
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException
from selenium.webdriver.chrome.options import Options

from finance.models import StockSymbol

logger = logging.getLogger(__name__)


class Morningstar:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(options=chrome_options)

    def login(self):
        """
        Log into Morningstar via selenium
        """
        username = os.environ.get('MS_USERNAME')
        password = os.environ.get('MS_PASSWORD')
        url = 'https://www.morningstar.com/sign-in'
        self.browser.get(url)
        time.sleep(3)
        self.browser.find_element('id', 'emailInput').send_keys(username)
        self.browser.find_element('id', 'passwordInput').send_keys(password)
        button = self.browser.find_element('class name', 'mds-button--primary___ctrsi')
        button.click()
        time.sleep(3)

    def update(self):
        self.login()
        current_stocks = StockSymbol.objects.all()
        days_to_ignore = []
        today = date.today()
        for x in range(10):
            days_to_ignore.append(today - timedelta(days=x))
            days_to_ignore.append(today + timedelta(days=x))

        for x in current_stocks:
            if x.update_date not in days_to_ignore:
                self.get_valuation(x.symbol, x.link)
            else:
                continue

        urls = ['https://www.morningstar.com/1-star-stocks',
                'https://www.morningstar.com/4-star-stocks',
                'https://www.morningstar.com/5-star-stocks',
                'https://www.morningstar.com/best-investments/five-star-stocks',
                'https://www.morningstar.com/best-investments/wide-moat-undervalued-stocks',
                'https://www.morningstar.com/best-investments/moats-on-sale',
                ]
        for url in urls:
            self.parse_prescreen(url, current_stocks)

    def parse_prescreen(self, url, current):
        links = [x.link for x in current]
        # Need to put into a list in case the link is paginated
        urls = [url]
        symbols = list()
        for url in urls:
            self.browser.get(url)

            # Append to list of urls if more than one page of results
            pages = self.browser.find_elements('class name', 'mds-pagination__item')
            for page in pages:
                url_link = page.find_element('tag name', 'a').get_attribute('href')
                if url_link in urls:
                    continue
                else:
                    urls.append(url_link)

            # Table rows will be tagged either 'tr' or 'mdc-table-row'
            table_rows = self.browser.find_elements('tag name', 'tr')
            if len(table_rows) == 0:
                table_rows = self.browser.find_elements('class name', 'mdc-table-row')
                tag_name = 'div'
            else:
                tag_name = 'td'
            del (table_rows[0])
            for row in table_rows:
                field = row.find_elements('tag name', tag_name)[1]
                ticker = field.text
                link = field.find_element('tag name', 'a').get_attribute('href')
                if any(x in link for x in ['xnys', 'xnas', 'xase']):
                    if link not in links:
                        symbols.append((ticker, link))
                        links.append(link)
        for ticker, link in symbols:
            self.get_valuation(ticker, link)

    def get_valuation(self, ticker, link):
        print(f'Getting valuation for {ticker}')
        fv = self.fair_value(ticker, link)
        if fv:
            data = {'symbol': ticker,
                    'fair_value': fv,
                    'uncertainty': self.uncertainty_rating(link),
                    'stars': self.star_rating(link),
                    'link': link,
                    'update_date': date.today()
                    }
            _, created = StockSymbol.objects.update_or_create(symbol=ticker, defaults=data)
            if created:
                logger.info(f'Added {ticker}')
        else:
            try:
                modify_entry = StockSymbol.objects.get(symbol=ticker)
                modify_entry.stars = 0
                modify_entry.save()
            except FieldError:
                print(f'{ticker} - Field Error')
            except ObjectDoesNotExist:
                pass
            except ValueError:
                print(f'{ticker} - Value Error')

    def fair_value(self, ticker, link):
        """
        Return Morningstar Fair Value estimate for given symbol.
        """
        try:
            if link != self.browser.current_url:
                self.browser.get(link)
                time.sleep(3.3)

            stock_title = self.browser.find_element('class name', 'stock__title-rating__mdc')
        except (InvalidArgumentException, NoSuchElementException):
            print(f'{ticker} is invalid')
            return

        try:
            stock_title.find_element('class name', 'mdc-star-rating__quant__mdc')
            print(f'Skipping {ticker} because "Q" value')
            return
        except NoSuchElementException:
            pass

        try:
            class_name = 'mdc-price-to-fair-value-summary__fair-value__mdc'
            div = self.browser.find_element('class name', f'{class_name}')
            fields = div.find_elements('class name', 'mdc-currency')
            fv = fields[0].text
            fv = fv.replace(',', '')
            fv = fv.replace('$', '')
            fv = float(fv)
            return fv
        except (IndexError, NoSuchElementException):
            return

    def uncertainty_rating(self, link):
        """
        Return uncertainty of fair value
        """
        if link != self.browser.current_url:
            self.browser.get(link)
            time.sleep(2.5)
        fv_box_class = 'mdc-price-to-fair-value-summary__fair-value__mdc'
        fv_box = self.browser.find_element('class name', fv_box_class)
        all_text = fv_box.find_elements('class name', 'mdc-locked-text__mdc')
        uncertainty = all_text[-1].text
        return uncertainty

    def star_rating(self, link):
        """
        Return integer of number of Morningstar Star Rating for symbol link
        """
        if link != self.browser.current_url:
            self.browser.get(link)
            time.sleep(2.5)
        # stars = len(self.browser.find_elements('class name', 'mdc-security-header__star'))
        stock_title = self.browser.find_element('class name', 'stock__title-rating__mdc')
        stars = len(stock_title.find_elements('class name', 'mdc-star-rating__star__mdc'))
        return stars
