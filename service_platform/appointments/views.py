from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

from accounts.decorators import staff_required, normal_user_required
from accounts.models import User
from services.models import Service
from tokens.services import debit_tokens
from notifications.utils import create_notification
from .models import Appointment, ServicePurchase, StaffAvailability
from .forms import AvailabilityForm, AppointmentForm


@normal_user_required
def purchase_service_view(request, service_id):
    """Purchase a non-call service immediately using tokens."""
    service = get_object_or_404(Service, id=service_id, status=Service.Status.APPROVED)

    if request.method != 'POST':
        return redirect('services:detail', service_id=service.id)

    try:
        with transaction.atomic():
            debit_tokens(
                request.user, service.token_price,
                performed_by=None,
                description=f'Purchased service: {service.title}'
            )
            now = timezone.now()
            purchase = ServicePurchase.objects.create(
                user=request.user,
                staff=service.staff,
                service=service,
                tokens_spent=service.token_price,
                activated_at=now,
                expires_at=now + timedelta(minutes=service.duration_minutes),
                status=ServicePurchase.Status.ACTIVE,
            )
            create_notification(
                service.staff,
                f'{request.user.full_name} purchased "{service.title}".',
                url=f'/services/{service.id}/'
            )
        messages.success(request, f'Service purchased! {service.token_price} tokens deducted.')
        return redirect('appointments:my_purchases')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('services:detail', service_id=service.id)


@normal_user_required
def book_appointment_view(request, service_id):
    """Book a call appointment for a call-type service."""
    service = get_object_or_404(Service, id=service_id, status=Service.Status.APPROVED)
    if service.service_type == Service.ServiceType.GENERAL:
        messages.error(request, 'This service is not a call service.')
        return redirect('services:detail', service_id=service.id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            scheduled_time = form.cleaned_data['scheduled_time']
            # Prevent overlapping appointments for the same staff
            conflict = Appointment.objects.filter(
                staff=service.staff,
                scheduled_time=scheduled_time,
                status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED, Appointment.Status.ONGOING]
            ).exists()
            if conflict:
                messages.error(request, 'That time slot is already booked. Please pick another.')
            else:
                try:
                    with transaction.atomic():
                        debit_tokens(
                            request.user, service.token_price,
                            description=f'Booked appointment: {service.title}'
                        )
                        appt = Appointment.objects.create(
                            user=request.user,
                            staff=service.staff,
                            service=service,
                            appointment_type=service.service_type,
                            scheduled_time=scheduled_time,
                            duration_minutes=service.duration_minutes,
                            status=Appointment.Status.PENDING,
                        )
                        create_notification(
                            service.staff,
                            f'New appointment request from {request.user.full_name} for "{service.title}".',
                            url=f'/appointments/{appt.id}/'
                        )
                    messages.success(request, 'Appointment booked! Awaiting staff confirmation.')
                    return redirect('appointments:detail', appointment_id=appt.id)
                except Exception as e:
                    messages.error(request, str(e))
    else:
        form = AppointmentForm()
    return render(request, 'appointments/book.html', {'form': form, 'service': service})


@login_required
def appointment_detail_view(request, appointment_id):
    """View an appointment (only user or staff involved can see)."""
    appt = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in (appt.user, appt.staff) and not request.user.is_super_admin:
        messages.error(request, 'You are not allowed to view this appointment.')
        return redirect('posts:home')
    return render(request, 'appointments/detail.html', {'appointment': appt})


@login_required
def my_appointments_view(request):
    """List user's or staff's appointments."""
    if request.user.is_staff_user or request.user.is_super_admin:
        appts = Appointment.objects.filter(staff=request.user)
    else:
        appts = Appointment.objects.filter(user=request.user)
    return render(request, 'appointments/my_appointments.html', {'appointments': appts})


@login_required
def my_purchases_view(request):
    """Show all services purchased by the current user."""
    purchases = ServicePurchase.objects.filter(user=request.user).select_related('service', 'staff')
    return render(request, 'appointments/my_purchases.html', {'purchases': purchases})


@staff_required
def confirm_appointment_view(request, appointment_id):
    appt = get_object_or_404(Appointment, id=appointment_id, staff=request.user)
    appt.status = Appointment.Status.CONFIRMED
    appt.save()
    create_notification(
        appt.user,
        f'Your appointment on {appt.scheduled_time:%Y-%m-%d %H:%M} was confirmed.',
        url=f'/appointments/{appt.id}/'
    )
    messages.success(request, 'Appointment confirmed.')
    return redirect('appointments:detail', appointment_id=appt.id)


@staff_required
def complete_appointment_view(request, appointment_id):
    appt = get_object_or_404(Appointment, id=appointment_id, staff=request.user)
    appt.status = Appointment.Status.COMPLETED
    appt.save()
    create_notification(
        appt.user, 'Your appointment is now complete. Please leave a review.',
        url=f'/reviews/create/{appt.id}/'
    )
    messages.success(request, 'Appointment marked as completed.')
    return redirect('appointments:detail', appointment_id=appt.id)


@login_required
def cancel_appointment_view(request, appointment_id):
    appt = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in (appt.user, appt.staff) and not request.user.is_super_admin:
        messages.error(request, 'Not allowed.')
        return redirect('appointments:my_appointments')
    appt.status = Appointment.Status.CANCELLED
    appt.save()
    messages.info(request, 'Appointment cancelled.')
    return redirect('appointments:my_appointments')


@staff_required
def manage_availability_view(request):
    """Staff can list/create/delete their weekly availability."""
    slots = StaffAvailability.objects.filter(staff=request.user)
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.staff = request.user
            slot.save()
            messages.success(request, 'Availability slot added.')
            return redirect('appointments:availability')
    else:
        form = AvailabilityForm()
    return render(request, 'appointments/availability.html', {'form': form, 'slots': slots})


@staff_required
def delete_availability_view(request, slot_id):
    slot = get_object_or_404(StaffAvailability, id=slot_id, staff=request.user)
    slot.delete()
    messages.success(request, 'Slot deleted.')
    return redirect('appointments:availability')