from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('report/<int:user_id>/', views.report_user_view, name='report_user'),
    path('block/<int:user_id>/', views.block_user_view, name='block_user'),
    path('unblock/<int:user_id>/', views.unblock_user_view, name='unblock_user'),
    path('list/', views.report_list_view, name='list'),
    path('<int:report_id>/resolve/', views.resolve_report_view, name='resolve'),
    path('account/<int:user_id>/block/', views.block_account_view, name='block_account'),
    path('account/<int:user_id>/unblock/', views.unblock_account_view, name='unblock_account'),
]