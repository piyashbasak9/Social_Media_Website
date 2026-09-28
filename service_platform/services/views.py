from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from accounts.decorators import staff_required, super_admin_required
from accounts.models import User
from .models import Service, ServiceMedia
from .forms import ServiceForm, ServiceMediaForm


def service_list_view(request):
    """Browse all approved services."""
    services = Service.objects.filter(status=Service.Status.APPROVED).select_related('staff')
    service_type = request.GET.get('type')
    if service_type in dict(Service.ServiceType.choices):
        services = services.filter(service_type=service_type)
    return render(request, 'services/list.html', {'services': services})


def service_detail_view(request, service_id):
    """Detail page for one service."""
    service = get_object_or_404(Service, id=service_id)
    # Non-approved services are only visible to owner/staff or super admin
    if service.status != Service.Status.APPROVED:
        if not request.user.is_authenticated:
            messages.error(request, 'This service is not yet available.')
            return redirect('services:list')
        if request.user != service.staff and not request.user.is_super_admin:
            messages.error(request, 'This service is not available.')
            return redirect('services:list')
    return render(request, 'services/detail.html', {'service': service})


@staff_required
def create_service_view(request):
    """Staff creates a new service (status = pending)."""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.staff = request.user
            service.status = Service.Status.PENDING
            service.save()
            messages.success(request, 'Service created. Waiting for admin approval.')
            return redirect('services:my_services')
    else:
        form = ServiceForm()
    return render(request, 'services/create.html', {'form': form})


@staff_required
def my_services_view(request):
    """List services created by the logged-in staff."""
    services = Service.objects.filter(staff=request.user)
    return render(request, 'services/my_services.html', {'services': services})


@staff_required
def edit_service_view(request, service_id):
    """Staff edits own service."""
    service = get_object_or_404(Service, id=service_id, staff=request.user)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            s = form.save(commit=False)
            # Reset status to pending on edit
            s.status = Service.Status.PENDING
            s.save()
            messages.success(request, 'Service updated. Pending admin re-approval.')
            return redirect('services:my_services')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'services/edit.html', {'form': form, 'service': service})


@staff_required
def delete_service_view(request, service_id):
    """Delete own service."""
    service = get_object_or_404(Service, id=service_id, staff=request.user)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted.')
        return redirect('services:my_services')
    return render(request, 'services/confirm_delete.html', {'service': service})


@staff_required
def upload_service_media_view(request, service_id):
    """Upload additional media to a service."""
    service = get_object_or_404(Service, id=service_id, staff=request.user)
    if request.method == 'POST':
        form = ServiceMediaForm(request.POST, request.FILES)
        if form.is_valid():
            media = form.save(commit=False)
            media.service = service
            media.save()
            messages.success(request, 'Media uploaded.')
            return redirect('services:upload_media', service_id=service.id)
    else:
        form = ServiceMediaForm()
    return render(request, 'services/upload_media.html', {
        'form': form, 'service': service, 'media_list': service.media.all()
    })


@super_admin_required
def pending_services_view(request):
    """Admin list of pending services."""
    services = Service.objects.filter(status=Service.Status.PENDING).select_related('staff')
    return render(request, 'services/pending.html', {'services': services})


@super_admin_required
def approve_service_view(request, service_id):
    """Admin approves service."""
    service = get_object_or_404(Service, id=service_id)
    service.status = Service.Status.APPROVED
    service.save()
    messages.success(request, f'Service "{service.title}" approved.')
    return redirect('services:pending')


@super_admin_required
def reject_service_view(request, service_id):
    """Admin rejects service."""
    service = get_object_or_404(Service, id=service_id)
    service.status = Service.Status.REJECTED
    service.save()
    messages.warning(request, f'Service "{service.title}" rejected.')
    return redirect('services:pending')


@super_admin_required
def disable_service_view(request, service_id):
    """Admin disables an active service."""
    service = get_object_or_404(Service, id=service_id)
    service.status = Service.Status.DISABLED
    service.save()
    messages.info(request, f'Service "{service.title}" disabled.')
    return redirect('services:list')