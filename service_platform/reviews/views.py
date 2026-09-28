from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg

from accounts.decorators import normal_user_required
from accounts.models import User
from profiles.models import StaffProfile
from appointments.models import Appointment
from notifications.utils import create_notification
from .models import Review
from .forms import ReviewForm


@normal_user_required
def create_review_view(request, appointment_id):
    """Normal user leaves review for a completed appointment."""
    appt = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    if appt.status != Appointment.Status.COMPLETED:
        messages.error(request, 'You can only review completed appointments.')
        return redirect('appointments:detail', appointment_id=appt.id)
    if hasattr(appt, 'review'):
        messages.info(request, 'You already reviewed this appointment.')
        return redirect('appointments:detail', appointment_id=appt.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appt
            review.user = request.user
            review.staff = appt.staff
            review.save()

            # Recalculate staff rating
            profile, _ = StaffProfile.objects.get_or_create(user=appt.staff)
            agg = Review.objects.filter(staff=appt.staff).aggregate(avg=Avg('rating'))
            profile.average_rating = round(agg['avg'] or 0, 2)
            profile.total_reviews = Review.objects.filter(staff=appt.staff).count()
            profile.save()

            create_notification(appt.staff, f'You received a new {review.rating}★ review.',
                                url=f'/profiles/staff/{appt.staff.id}/')
            messages.success(request, 'Thank you for your review!')
            return redirect('appointments:detail', appointment_id=appt.id)
    else:
        form = ReviewForm()
    return render(request, 'reviews/create.html', {'form': form, 'appointment': appt})