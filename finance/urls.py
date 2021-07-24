from finance import views
from django.urls import path


urlpatterns = [
    path('update/', views.update),
    path('options/', views.options),
]
