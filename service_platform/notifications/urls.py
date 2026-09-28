from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.list_notifications_view, name='list'),
    path('<int:notification_id>/read/', views.mark_read_view, name='read'),
    path('read-all/', views.mark_all_read_view, name='read_all'),
]