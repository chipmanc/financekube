from django.shortcuts import render
from django.http import HttpResponse
from asgiref.sync import sync_to_async

from finance.models import StockSymbol
from finance.utils import morningstar, tdameritrade


def _update(request):
    morningstar.update()
    return HttpResponse("DONE")


update = sync_to_async(_update)


def _options(request):
    good_stocks = StockSymbol.objects.filter(stars__gte=4)
    bad_stocks = StockSymbol.objects.filter(stars__exact=1)
    tdameritrade.option_screen(good_stocks, bad_stocks)
    return HttpResponse("DONE")


options = sync_to_async(_options)
