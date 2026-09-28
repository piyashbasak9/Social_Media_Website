from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import super_admin_required
from accounts.models import User
from .models import Report, Block
from .forms import ReportForm


@login_required
def report_user_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, 'You cannot report yourself.')
        return redirect('posts:home')
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.reporter = request.user
            r.reported_user = target
            r.save()
            messages.success(request, 'Report submitted. Admin will review it.')
            return redirect('posts:home')
    else:
        form = ReportForm()
    return render(request, 'reports/report.html', {'form': form, 'target': target})


@login_required
def block_user_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return redirect('posts:home')
    Block.objects.get_or_create(blocker=request.user, blocked=target)
    messages.success(request, f'You blocked {target.full_name}.')
    return redirect('posts:home')


@login_required
def unblock_user_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    Block.objects.filter(blocker=request.user, blocked=target).delete()
    messages.info(request, f'You unblocked {target.full_name}.')
    return redirect('posts:home')


@super_admin_required
def report_list_view(request):
    reports = Report.objects.all().select_related('reporter', 'reported_user')
    return render(request, 'reports/list.html', {'reports': reports})


@super_admin_required
def resolve_report_view(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.status = Report.Status.RESOLVED
    report.save()
    messages.success(request, 'Report marked as resolved.')
    return redirect('reports:list')


@super_admin_required
def block_account_view(request, user_id):
    u = get_object_or_404(User, id=user_id)
    u.is_blocked = True
    u.is_active = False
    u.save()
    messages.warning(request, f'{u.email} blocked.')
    return redirect('reports:list')


@super_admin_required
def unblock_account_view(request, user_id):
    u = get_object_or_404(User, id=user_id)
    u.is_blocked = False
    u.is_active = True
    u.save()
    messages.success(request, f'{u.email} unblocked.')
    return redirect('reports:list')