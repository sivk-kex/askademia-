from django import forms
from .models import ChatbotConfig

class ChatbotConfigForm(forms.ModelForm):
    class Meta:
        model = ChatbotConfig
        fields = ['name', 'welcome_message', 'confidence_threshold', 'enable_web_links']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'confidence_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'max': '0.9',
                'step': '0.05'
            }),
            'enable_web_links': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }