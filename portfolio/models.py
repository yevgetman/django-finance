from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid
import secrets

class User(AbstractUser):
    """
    Custom user model with API key authentication support.
    Users don't log in through traditional means but use API keys.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    is_api_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_api_access = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'portfolio_user'
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_api_key():
        """Generate a secure random API key"""
        return secrets.token_urlsafe(48)
    
    def regenerate_api_key(self):
        """Generate a new API key for this user"""
        self.api_key = self.generate_api_key()
        self.save(update_fields=['api_key'])
        return self.api_key
    
    def update_last_access(self):
        """Update the last API access timestamp"""
        self.last_api_access = timezone.now()
        self.save(update_fields=['last_api_access'])
    
    def __str__(self):
        return f"{self.username} ({self.email})"

class Conversation(models.Model):
    """
    Model for storing conversation threads with the OpenAI API.
    Each conversation represents a single thread of analysis or recommendations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    openai_thread_id = models.CharField(max_length=255, unique=True)
    conversation_type = models.CharField(
        max_length=20,
        choices=[
            ('analysis', 'Portfolio Analysis'),
            ('recommendations', 'Portfolio Recommendations'),
            ('chat', 'Chat'),
        ],
        default='analysis'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    # Store the last portfolio data as JSON to provide context for the conversation
    last_portfolio_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_updated']
        
    def __str__(self):
        return f"{self.conversation_type.title()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        
    def mark_updated(self):
        """Update the last_updated timestamp"""
        self.last_updated = timezone.now()
        self.save(update_fields=['last_updated'])
