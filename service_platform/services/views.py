import mimetypes

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.views.decorators.http import require_POST

from accounts.decorators import normal_user_required, staff_required, super_admin_required
from accounts.models import User
from tokens.services import debit_tokens
from .models import Service, ServiceMedia, ServiceUnlock
from .forms import ServiceForm, ServiceMediaForm


def service_list_view(request):
    """Browse approved Photo and Video services with locked previews."""
    services = Service.objects.filter(
        status=Service.Status.APPROVED,
        service_type=Service.ServiceType.GENERAL,
        staff__role=User.Role.STAFF,
    ).select_related('staff').prefetch_related(
        Prefetch(
            'media',
            queryset=ServiceMedia.objects.filter(thumbnail__isnull=False).exclude(thumbnail=''),
            to_attr='preview_media',
        )
    )
    unlocked_service_ids = set()
    if request.user.is_authenticated and request.user.is_normal_user:
        unlocked_service_ids = set(
            ServiceUnlock.objects.filter(user=request.user).values_list('service_id', flat=True)
        )
    return render(request, 'services/list.html', {
        'services': services,
        'unlocked_service_ids': unlocked_service_ids,
    })


def service_detail_view(request, service_id):
    """Show service details without exposing its protected gallery."""
    service = get_object_or_404(Service, id=service_id)
    if request.user.is_authenticated and request.user.is_normal_user and service.staff.role != User.Role.STAFF:
        raise Http404
    if service.staff.role != User.Role.STAFF and not (
        request.user.is_authenticated and (request.user == service.staff or request.user.is_super_admin)
    ):
        raise Http404
    if service.service_type != Service.ServiceType.GENERAL:
        messages.error(request, 'Only Photo and Video services are available.')
        return redirect('services:list')
    # Non-approved services are only visible to owner/staff or super admin
    if service.status != Service.Status.APPROVED:
        if not request.user.is_authenticated:
            messages.error(request, 'This service is not yet available.')
            return redirect('services:list')
        if request.user != service.staff and not request.user.is_super_admin:
            messages.error(request, 'This service is not available.')
            return redirect('services:list')
    unlocked = request.user.is_authenticated and ServiceUnlock.objects.filter(
        user=request.user, service=service
    ).exists()
    return render(request, 'services/detail.html', {'service': service, 'unlocked': unlocked})


@normal_user_required
@require_POST
def unlock_service_view(request, service_id):
    """Charge tokens once and grant persistent access to an approved gallery."""
    try:
        with transaction.atomic():
            service = get_object_or_404(
                Service.objects.select_for_update(),
                id=service_id,
                status=Service.Status.APPROVED,
                service_type=Service.ServiceType.GENERAL,
                staff__role=User.Role.STAFF,
            )
            unlock, created = ServiceUnlock.objects.get_or_create(
                user=request.user, service=service
            )
            if created:
                debit_tokens(
                    request.user,
                    service.token_price,
                    description=f'Unlocked service: {service.title}',
                )
    except ValidationError as error:
        messages.error(request, str(error))
        return redirect('services:list')

    if created:
        messages.success(request, f'"{service.title}" unlocked. You can now view its gallery.')
    else:
        messages.info(request, f'"{service.title}" is already unlocked.')
    return redirect('services:list')


@login_required
def service_view_view(request, service_id):
    """Display the photos and videos after access has been unlocked."""
    service = get_object_or_404(
        Service.objects.prefetch_related('media'),
        id=service_id,
        service_type=Service.ServiceType.GENERAL,
    )
    is_owner_or_admin = request.user == service.staff or request.user.is_super_admin
    if request.user.is_normal_user and service.staff.role != User.Role.STAFF:
        raise Http404
    if service.staff.role != User.Role.STAFF and not is_owner_or_admin:
        raise Http404
    if service.status != Service.Status.APPROVED and not is_owner_or_admin:
        messages.error(request, 'This service is not available.')
        return redirect('services:list')
    has_access = is_owner_or_admin or ServiceUnlock.objects.filter(
        user=request.user, service=service
    ).exists()
    if not has_access:
        messages.error(request, 'Unlock this service before viewing its media.')
        return redirect('services:detail', service_id=service.id)
    return render(request, 'services/view.html', {'service': service})


@login_required
def service_media_file_view(request, media_id):
    """Serve a service media file only to its owner, admins, or unlocked users."""
    media = get_object_or_404(ServiceMedia.objects.select_related('service'), id=media_id)
    service = media.service
    is_owner_or_admin = request.user == service.staff or request.user.is_super_admin
    if request.user.is_normal_user and service.staff.role != User.Role.STAFF:
        raise Http404
    if service.staff.role != User.Role.STAFF and not is_owner_or_admin:
        raise Http404
    has_access = is_owner_or_admin or (
        service.status == Service.Status.APPROVED
        and ServiceUnlock.objects.filter(user=request.user, service=service).exists()
    )
    if not has_access:
        return HttpResponseForbidden('Unlock this service to access its media.')
    content_type = mimetypes.guess_type(media.file.name)[0] or 'application/octet-stream'
    return FileResponse(media.file.open('rb'), content_type=content_type)


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
            messages.success(request, 'Service created. Activate it from My Services when it is ready.')
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
@require_POST
def toggle_service_status_view(request, service_id):
    """Let a service owner activate or deactivate their own service."""
    service = get_object_or_404(Service, id=service_id, staff=request.user)
    if service.status == Service.Status.APPROVED:
        service.status = Service.Status.DISABLED
        message = f'Service "{service.title}" deactivated.'
    else:
        service.status = Service.Status.APPROVED
        message = f'Service "{service.title}" activated.'
    service.save(update_fields=['status'])
    messages.success(request, message)
    return redirect('services:my_services')


@staff_required
def edit_service_view(request, service_id):
    """Staff edits own service."""
    service = get_object_or_404(Service, id=service_id, staff=request.user)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated.')
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