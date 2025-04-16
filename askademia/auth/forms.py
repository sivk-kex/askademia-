from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['institution_name', 'institution_type']
        widgets = {
            'institution_name': forms.TextInput(attrs={'class': 'form-control'}),
            'institution_type': forms.Select(attrs={'class': 'form-control'}),
        }