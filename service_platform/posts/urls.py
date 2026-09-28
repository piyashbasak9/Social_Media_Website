from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('post/<int:post_id>/', views.post_detail_view, name='detail'),
    path('post/create/', views.create_post_view, name='create'),
    path('post/<int:post_id>/edit/', views.edit_post_view, name='edit'),
    path('post/<int:post_id>/delete/', views.delete_post_view, name='delete'),
    path('post/<int:post_id>/like/', views.like_post_view, name='like'),
    path('post/<int:post_id>/comment/', views.comment_post_view, name='comment'),
]