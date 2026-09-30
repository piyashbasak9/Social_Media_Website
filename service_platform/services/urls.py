from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list_view, name='list'),
    path('<int:service_id>/', views.service_detail_view, name='detail'),
    path('<int:service_id>/unlock/', views.unlock_service_view, name='unlock'),
    path('<int:service_id>/view/', views.service_view_view, name='view'),
    path('media/<int:media_id>/', views.service_media_file_view, name='media_file'),
    path('create/', views.create_service_view, name='create'),
    path('mine/', views.my_services_view, name='my_services'),
    path('<int:service_id>/toggle-status/', views.toggle_service_status_view, name='toggle_status'),
    path('<int:service_id>/edit/', views.edit_service_view, name='edit'),
    path('<int:service_id>/delete/', views.delete_service_view, name='delete'),
    path('<int:service_id>/media/', views.upload_service_media_view, name='upload_media'),
    path('admin/pending/', views.pending_services_view, name='pending'),
    path('admin/<int:service_id>/approve/', views.approve_service_view, name='approve'),
    path('admin/<int:service_id>/reject/', views.reject_service_view, name='reject'),
    path('admin/<int:service_id>/disable/', views.disable_service_view, name='disable'),
]