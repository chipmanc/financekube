# from django.shortcuts import render
from django.http import HttpResponse
from asgiref.sync import sync_to_async

from finance.models import StockSymbol
from finance.utils import morningstar, schwab

def _stock_symbol_update(request):
    ms = morningstar.Morningstar()
    ms.update()
    return HttpResponse("DONE")


stock_symbol_update = sync_to_async(_stock_symbol_update)


def _option_screen(request, symbol=None):
    if symbol:
        symbol = StockSymbol.objects.get(symbol__exact=symbol)
        schwab.option_screen([symbol])
    else:
        good_stocks = StockSymbol.objects.filter(stars__gte=4).order_by('symbol')
        bad_stocks = StockSymbol.objects.filter(stars__exact=1).order_by('symbol')
        schwab.option_screen(good_stocks)
        schwab.option_screen(bad_stocks)
    return HttpResponse("DONE")


option_screen = sync_to_async(_option_screen)


def _option_update(request):
    schwab.option_update()
    return HttpResponse("DONE")


option_update = sync_to_async(_option_update)

