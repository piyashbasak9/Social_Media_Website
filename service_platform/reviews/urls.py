from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('create/<int:appointment_id>/', views.create_review_view, name='create'),
]