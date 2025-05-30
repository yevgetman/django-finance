from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_portfolio, name='analyze-portfolio'),
    path('ticker-info/', views.get_ticker_info, name='ticker-info'),
]
