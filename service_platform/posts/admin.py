from django.contrib import admin
from .models import Post, PostMedia, Like, Comment


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'staff', 'created_at')
    inlines = [PostMediaInline]


admin.site.register(Like)
admin.site.register(Comment)