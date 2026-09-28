from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('<int:user_id>/', views.conversation_view, name='conversation'),
]