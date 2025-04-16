from django.db import models
from django.contrib.auth.models import User

class ChatbotConfig(models.Model):
    """Chatbot configuration for specific user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chatbot_config')
    name = models.CharField(max_length=100, default='AI Assistant')
    welcome_message = models.TextField(default='Hello! I am Askademia! How can I help you today?')
    confidence_threshold = models.FloatField(default=0.7)  # 70% threshold for response confidence
    enable_web_links = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    embed_code = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Companion"

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Chat Session {self.session_id}"

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True)  # Only for assistant messages
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.message_type} message in {self.session}"

class KnowledgeGap(models.Model):
    """Tracks questions the chatbot couldn't answer confidently"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_gaps')
    question = models.TextField()
    confidence_score = models.FloatField()
    chat_message = models.OneToOneField(ChatMessage, on_delete=models.CASCADE, related_name='knowledge_gap')
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Gap: {self.question[:50]}..."