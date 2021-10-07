# from django.shortcuts import render
from django.http import HttpResponse
from asgiref.sync import sync_to_async

from finance.models import StockSymbol
from finance.utils import morningstar, tdameritrade


def _stock_symbol_update(request):
    ms = morningstar.Morningstar()
    ms.update()
    return HttpResponse("DONE")


stock_symbol_update = sync_to_async(_stock_symbol_update)


def _option_screen(request):
    good_stocks = StockSymbol.objects.filter(stars__gte=4)
    bad_stocks = StockSymbol.objects.filter(stars__exact=1)
    tdameritrade.option_screen(good_stocks, bad_stocks)
    return HttpResponse("DONE")


option_screen = sync_to_async(_option_screen)


def _option_update(request):
    tdameritrade.option_update()
    return HttpResponse("DONE")


option_update = sync_to_async(_option_update)
