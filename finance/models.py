from datetime import date

from django.db import models


class StockSymbol(models.Model):
    symbol = models.CharField(max_length=8, primary_key=True)
    fair_value = models.FloatField()
    stars = models.PositiveSmallIntegerField()
    uncertainty = models.CharField(max_length=10)
    link = models.URLField()
    update_date = models.DateField(default=date.today)


class Option(models.Model):
    symbol = models.CharField(max_length=25)
    ticker = models.ForeignKey(StockSymbol, on_delete=models.SET_NULL, null=True)
    date = models.DateField(auto_now=True)
    buy = models.FloatField(null=True)
    sell = models.FloatField(null=True)
    stddev = models.FloatField()
    cdf = models.FloatField()
    pdf = models.FloatField()
    strike_discount = models.FloatField()
    profit_percent = models.FloatField()
    cagr = models.FloatField(default=None)
    days_to_exp = models.PositiveSmallIntegerField()
    screened = models.BooleanField(default=False)
    sold = models.PositiveSmallIntegerField(null=True)
    expired = models.BooleanField(default=False)
