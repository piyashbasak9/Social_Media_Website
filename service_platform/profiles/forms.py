from django import forms
from .models import NormalUserProfile, StaffProfile


class NormalProfileForm(forms.ModelForm):
    class Meta:
        model = NormalUserProfile
        fields = ['profile_photo', 'bio', 'age', 'gender']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['profile_photo', 'cover_photo', 'bio', 'age', 'location', 'is_online']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'cover_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }