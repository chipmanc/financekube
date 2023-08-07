from finance import views
from django.urls import path, re_path


urlpatterns = [
    path('stock_symbol_update/', views.stock_symbol_update),
    re_path(r'^option_screen/(?P<symbol>\w+)$', views.option_screen),
    path('option_screen/', views.option_screen),
    path('option_update/', views.option_update),
]
