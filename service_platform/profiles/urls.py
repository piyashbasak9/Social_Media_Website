from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('me/', views.my_profile_view, name='my_profile'),
    path('edit/', views.edit_profile_view, name='edit_profile'),
    path('staff/<int:user_id>/', views.staff_profile_view, name='staff_profile'),
    path('user/<int:user_id>/', views.normal_profile_view, name='normal_profile'),
]