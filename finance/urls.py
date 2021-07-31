from finance import views
from django.urls import path


urlpatterns = [
    path('stock_symbol_update/', views.stock_symbol_update),
    path('option_screen/', views.option_screen),
    path('option_update/', views.option_update),
]
