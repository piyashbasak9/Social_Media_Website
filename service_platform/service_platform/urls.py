"""
URL configuration for service_platform project.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    return redirect('accounts:login')


urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('posts/', include('posts.urls')),
    path('profiles/', include('profiles.urls')),
    path('services/', include('services.urls')),
    path('appointments/', include('appointments.urls')),
    path('notifications/', include('notifications.urls')),
    path('chat/', include('chat.urls')),
    path('tokens/', include('tokens.urls')),
    path('reviews/', include('reviews.urls')),
    path('reports/', include('reports.urls')),
]
