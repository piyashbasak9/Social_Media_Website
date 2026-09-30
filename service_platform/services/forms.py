from django import forms
from .models import Service, ServiceMedia


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'description', 'token_price', 'service_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'token_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_token_price(self):
        price = self.cleaned_data['token_price']
        if price <= 0:
            raise forms.ValidationError('Token price must be greater than 0.')
        return price

class ServiceMediaForm(forms.ModelForm):
    """Upload one media file for a service (called multiple times)."""

    class Meta:
        model = ServiceMedia
        fields = ['media_type', 'file', 'thumbnail', 'display_order']
        widgets = {
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    # File size / type validation
    ALLOWED_IMAGE = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    ALLOWED_VIDEO = ['video/mp4', 'video/webm', 'video/quicktime']
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB

    def clean(self):
        cleaned = super().clean()
        media_type = cleaned.get('media_type')
        file = cleaned.get('file')
        if not file:
            return cleaned

        if file.size > self.MAX_SIZE:
            raise forms.ValidationError('File size must be under 10 MB.')

        content_type = getattr(file, 'content_type', '')
        if media_type == 'image' and content_type not in self.ALLOWED_IMAGE:
            raise forms.ValidationError('Unsupported image type.')
        if media_type == 'video' and content_type not in self.ALLOWED_VIDEO:
            raise forms.ValidationError('Unsupported video type.')
        return cleaned