from django.urls import path
from . import views

app_name = 'tokens'

urlpatterns = [
    path('', views.my_tokens_view, name='my_tokens'),
    path('give/', views.give_tokens_view, name='give'),
    path('adjust/', views.adjust_tokens_view, name='adjust'),
    path('all/', views.all_transactions_view, name='all_transactions'),
]