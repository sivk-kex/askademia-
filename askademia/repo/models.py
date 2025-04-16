import os
import uuid
from django.db import models
from django.contrib.auth.models import User

def get_file_path(instance, filename):
    """Generate a unique file path for uploaded content"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    folder = instance.folder.folder_path if instance.folder else 'uncategorized'
    return os.path.join('repository', folder, filename)

class Folder(models.Model):
    """Repository folder for organizing content"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    folder_path = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Content(models.Model):
    """Repository content item (file or web link)"""
    CONTENT_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('link', 'Web Link'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    file = models.FileField(upload_to=get_file_path, blank=True, null=True)
    web_link = models.URLField(blank=True, null=True)
    extracted_text = models.TextField(blank=True, null=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='contents', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contents')
    vector_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Override save to handle file path changes"""
        if self.pk:
            old_instance = Content.objects.get(pk=self.pk)
            if old_instance.folder != self.folder and self.file:
                old_file_path = self.file.path
                self.file.name = get_file_path(self, os.path.basename(self.file.name))
                super().save(*args, **kwargs)
                if os.path.isfile(old_file_path):
                    new_file_path = self.file.path
                    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                    os.rename(old_file_path, new_file_path)
                return
        super().save(*args, **kwargs)