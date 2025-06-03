from django.db import models
from django.utils import timezone
import uuid

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
