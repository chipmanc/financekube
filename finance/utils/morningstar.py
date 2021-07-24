import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from finance.models import StockSymbol

logger = logging.getLogger(__name__)

chrome_options = Options()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(options=chrome_options)


def login():
    """
    Log into Morningstar via selenium
    """
    username = os.environ.get('MS_USERNAME')
    password = os.environ.get('MS_PASSWORD')
    url = 'https://www.morningstar.com/sign-in'
    browser.get(url)
    time.sleep(2)
    browser.find_element_by_id('emailInput').send_keys(username)
    browser.find_element_by_id('passwordInput').send_keys(password)
    button = browser.find_element_by_class_name('mds-button--primary___ctrsi')
    button.click()
    time.sleep(3)


def update():
    login()
    current_stocks = StockSymbol.objects.all()
    for x in current_stocks:
        get_valuation(x.symbol, x.link)

    urls = ['https://www.morningstar.com/1-star-stocks',
            'https://www.morningstar.com/4-star-stocks',
            'https://www.morningstar.com/5-star-stocks',
            'https://www.morningstar.com/best-investments/five-star-stocks',
            'https://www.morningstar.com/best-investments/wide-moat-undervalued-stocks',
            'https://www.morningstar.com/best-investments/moats-on-sale',
            ]
    for url in urls:
        parse_prescreen(url, current_stocks)


def parse_prescreen(url, current):
    links = [x.link for x in current]
    # Need to put into a list in case the link is paginated
    urls = [url]
    symbols = list()
    for url in urls:
        browser.get(url)

        # Append to list of urls if more than one page of results
        pages = browser.find_elements_by_class_name('mds-pagination__item')
        for page in pages:
            url_link = page.find_element_by_tag_name('a').get_attribute('href')
            if url_link in urls:
                continue
            else:
                urls.append(url_link)

        # Table rows will be tagged either 'tr' or 'mdc-table-row'
        table_rows = browser.find_elements_by_tag_name('tr')
        if len(table_rows) == 0:
            table_rows = browser.find_elements_by_class_name('mdc-table-row')
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
    for ticker, link in symbols:
        get_valuation(ticker, link)


def get_valuation(ticker, link):
    fv = fair_value(link)
    if fv:
        data = {'symbol': ticker,
                'fair_value': fv,
                'uncertainty': uncertainty_rating(link),
                'stars': star_rating(link),
                'link': link
                }
        _, created = StockSymbol.objects.update_or_create(symbol=ticker, defaults=data)
        if created:
            logger.info(f'Added {ticker}')
    else:
        remove_entry = StockSymbol(ticker)
        remove_entry.delete()


def fair_value(link):
    """
    Return Morningstar Fair Value estimate for given symbol.
    """
    if link != browser.current_url:
        browser.get(link)
        time.sleep(1)
    fields = browser.find_elements_by_tag_name('tspan')
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


def uncertainty_rating(link):
    """
    Return uncertainty of fair value
    """
    if link != browser.current_url:
        browser.get(link)
        time.sleep(1)
    try:
        fields = browser.find_elements_by_tag_name('tspan')
        uncertainty = fields[3].text.split(':')[1]
    except IndexError:
        uncertainty = 'Very'
    return uncertainty


def star_rating(link):
    """
    Return integer of number of Morningstar Star Rating for symbol link
    """
    if link != browser.current_url:
        browser.get(link)
        time.sleep(1)
    stars = browser.find_element_by_class_name('mdc-security-header__star-rating')
    stars = len(stars.find_elements_by_tag_name('svg'))
    return stars
