from django import forms
from .models import Post, PostMedia, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['caption']
        widgets = {
            'caption': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                             'placeholder': 'Write a caption...'}),
        }


class PostMediaForm(forms.ModelForm):
    class Meta:
        model = PostMedia
        fields = ['media_type', 'file', 'display_order']
        widgets = {
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write a comment...'})
        }