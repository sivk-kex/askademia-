from django.db import models
from django.contrib.auth.models import User
# Used this as this model as it would increase scope of usage of the app 

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    institution_name = models.CharField(max_length=200, blank=True, null=True)
    institution_type = models.CharField(max_length=50, choices=[
        ('university', 'University'),
        ('college', 'College'),
        ('school', 'School'),
        ('training_center', 'Training Center'),
        ('other', 'Other'),
    ], default='university')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    