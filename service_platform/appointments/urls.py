from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.my_appointments_view, name='my_appointments'),
    path('purchases/', views.my_purchases_view, name='my_purchases'),
    path('purchase/<int:service_id>/', views.purchase_service_view, name='purchase'),
    path('book/<int:service_id>/', views.book_appointment_view, name='book'),
    path('<int:appointment_id>/', views.appointment_detail_view, name='detail'),
    path('<int:appointment_id>/confirm/', views.confirm_appointment_view, name='confirm'),
    path('<int:appointment_id>/complete/', views.complete_appointment_view, name='complete'),
    path('<int:appointment_id>/cancel/', views.cancel_appointment_view, name='cancel'),
    path('availability/', views.manage_availability_view, name='availability'),
    path('availability/<int:slot_id>/delete/', views.delete_availability_view, name='delete_availability'),
]