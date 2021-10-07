import logging
import os
import time

from django.core.exceptions import FieldError, ObjectDoesNotExist
from selenium import webdriver
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
        self.browser.find_element_by_id('emailInput').send_keys(username)
        self.browser.find_element_by_id('passwordInput').send_keys(password)
        button = self.browser.find_element_by_class_name('mds-button--primary___ctrsi')
        button.click()
        time.sleep(3)

    def update(self):
        self.login()
        current_stocks = StockSymbol.objects.all()
        for x in current_stocks:
            self.get_valuation(x.symbol, x.link)

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
            pages = self.browser.find_elements_by_class_name('mds-pagination__item')
            for page in pages:
                url_link = page.find_element_by_tag_name('a').get_attribute('href')
                if url_link in urls:
                    continue
                else:
                    urls.append(url_link)

            # Table rows will be tagged either 'tr' or 'mdc-table-row'
            table_rows = self.browser.find_elements_by_tag_name('tr')
            if len(table_rows) == 0:
                table_rows = self.browser.find_elements_by_class_name('mdc-table-row')
                tag_name = 'div'
            else:
                tag_name = 'td'
            del (table_rows[0])
            for row in table_rows:
                field = row.find_elements_by_tag_name(tag_name)[1]
                ticker = field.text
                link = field.find_element_by_tag_name('a').get_attribute('href')
                if any(x in link for x in ['xnys', 'xnas', 'xase']):
                    if link not in links:
                        symbols.append((ticker, link))
                        links.append(link)
        for ticker, link in symbols:
            self.get_valuation(ticker, link)

    def get_valuation(self, ticker, link):
        print(f'Getting valuation for {ticker}')
        fv = self.fair_value(link)
        if fv:
            data = {'symbol': ticker,
                    'fair_value': fv,
                    'uncertainty': self.uncertainty_rating(link),
                    'stars': self.star_rating(link),
                    'link': link
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


    def fair_value(self, link):
        """
        Return Morningstar Fair Value estimate for given symbol.
        """
        if link != self.browser.current_url:
            self.browser.get(link)
            time.sleep(3)
        fields = self.browser.find_elements_by_tag_name('tspan')
        try:
            if fields[2].text in ['', 'Q']:
                return
            else:
                fv = fields[2].text
                fv = fv.replace(',', '')
                fv = float(fv)
            return fv
        except IndexError:
            return

    def uncertainty_rating(self, link):
        """
        Return uncertainty of fair value
        """
        if link != self.browser.current_url:
            self.browser.get(link)
            time.sleep(2.5)
        try:
            fields = self.browser.find_elements_by_tag_name('tspan')
            uncertainty = fields[3].text.split(':')[1]
        except IndexError:
            uncertainty = 'Very'
        return uncertainty

    def star_rating(self, link):
        """
        Return integer of number of Morningstar Star Rating for symbol link
        """
        if link != self.browser.current_url:
            self.browser.get(link)
            time.sleep(2.5)
        stars = self.browser.find_element_by_class_name('mdc-security-header__star-rating')
        stars = len(stars.find_elements_by_tag_name('svg'))
        return stars
