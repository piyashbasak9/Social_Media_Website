from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.decorators import staff_required
from accounts.models import User
from services.models import Service
from .models import Post, PostMedia, Like, Comment
from .forms import PostForm, PostMediaForm, CommentForm


def home_view(request):
    """Home feed with posts + approved services."""
    posts = Post.objects.select_related('staff').prefetch_related('media', 'likes', 'comments')
    services = Service.objects.filter(
        status=Service.Status.APPROVED,
        service_type=Service.ServiceType.GENERAL,
    ).select_related('staff')[:8]
    return render(request, 'posts/home.html', {'posts': posts, 'featured_services': services})


def post_detail_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'posts/detail.html', {'post': post, 'comment_form': CommentForm()})


@staff_required
def create_post_view(request):
    """Staff can create a post with optional media."""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.staff = request.user
            post.save()

            # Handle multiple file uploads (simple approach)
            files = request.FILES.getlist('media_files')
            for idx, f in enumerate(files):
                content_type = getattr(f, 'content_type', '')
                media_type = 'video' if content_type.startswith('video') else 'image'
                PostMedia.objects.create(
                    post=post, media_type=media_type, file=f, display_order=idx
                )
            messages.success(request, 'Post created.')
            return redirect('posts:home')
    else:
        form = PostForm()
    return render(request, 'posts/create.html', {'form': form})


@staff_required
def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, staff=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated.')
            return redirect('posts:detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/edit.html', {'form': form, 'post': post})


@staff_required
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, staff=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted.')
        return redirect('posts:home')
    return render(request, 'posts/confirm_delete.html', {'post': post})


@login_required
@require_POST
def like_post_view(request, post_id):
    """Like / unlike a post (AJAX friendly)."""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.like_count})


@login_required
@require_POST
def comment_post_view(request, post_id):
    """Add a comment to a post."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        c = form.save(commit=False)
        c.post = post
        c.user = request.user
        c.save()
        messages.success(request, 'Comment added.')
    return redirect('posts:detail', post_id=post.id)