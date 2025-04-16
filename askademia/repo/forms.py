from django import forms
from .models import Folder, Content

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'description', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(FolderForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['parent'].queryset = Folder.objects.filter(user=user)
            self.fields['parent'].required = False

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'description', 'content_type', 'file', 'web_link', 'folder']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'web_link': forms.URLInput(attrs={'class': 'form-control'}),
            'folder': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ContentForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['folder'].queryset = Folder.objects.filter(user=user)
            self.fields['folder'].required = False
        self.fields['file'].required = False
        self.fields['web_link'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        file = cleaned_data.get('file')
        web_link = cleaned_data.get('web_link')
        if content_type in ['text', 'image', 'video', 'pdf'] and not file:
            self.add_error('file', f'A file is required for {content_type} content type.')
        
        if content_type == 'link' and not web_link:
            self.add_error('web_link', 'A web link is required for link content type.')
        
        return cleaned_data