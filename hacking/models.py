from django.db import models
from django.contrib.auth import get_user_model

import uuid

User = get_user_model()

class SecurityDemo(models.Model):
    CATEGORY_CHOICES = (
        ('sql_injection', 'SQL Injection'),
        ('xss', 'Cross-Site Scriptin (XSS)'),
        ('csrf', 'CSRF Protection'),
        ('authentication', 'Authentication'),
        ('encryption', 'Encryption'),
    )

    id = models.UUIDField(primary_key=True , default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    vulnerable_code =  models.TextField(help_text="Vulnerable code example")
    secure_code = models.TextField(help_text="Secure code example")
    explanation = models.TextField(help_text="Detailed Explanation")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        db_table = 'security_demos'
        ordering = ['category', 'title']

    def __str__(self):
        return self.title


class UserSecurity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_activities')
    activity_type = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'user_security_activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"