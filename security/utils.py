import hashlib
import json

def generate_device_fingerprint(request):
    components = [
        request.Meta.get('HTTP_USER_AGENT', ''),
        request.Meta.get('HTTP_ACCEPT_LANGUAGE', ''),
        request.Meta.get('HTTP_ACCEPT_ENCODING', ''),
    ]

    fingerprint_string = ''.join(components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def detect_bot(user_agent):
    # basic bot detection
    bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
    user_agent_lower = user_agent.lower()

    for indicator in bot_indicators:
        if indicator in user_agent_lower:
            return True
    return False