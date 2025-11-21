import time

from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

from django.shortcuts import HttpResponse

class SecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Rate limiting
        ip = self.get_client_ip(request)
        key = f'rate_limit: {ip}'

        requests = cache.get(key, 0)
        if requests > 100:
            return HttpResponse('Rate limit exceeded', status=429)
        
        cache.set(key, requests + 1, 60)
    
    def process_response(self, request, response):
        # security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_F0R')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip