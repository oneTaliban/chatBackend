import threading
import time 
import random
import logging 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SeoBooster:
    def __init__(self):
        self.search_sessions = {}
        self.trend_operations = {}
        self.search_engines = {
            'google': 'https://www.google.com/search?q=',
            'bing': 'https://www.bing.com/search?q=',
            'yahoo': 'https://search.yahoo.com/search?q=',
            'duckduckgo': 'https://duckduckgo.com/q',
        }
    
    def generate_search_queries(self, keyword, variations):
        base_queries = [
            f"{keyword}",
            f"what is {keyword}",
            f"{keyword} news",
            f"latest {keyword}",
            f'{keyword} update',
            f"{keyword} 2025",
            f"{keyword} today"
            f"about {keyword}",
            f"{keyword} information",
            f"{keyword} details",
            f"{keyword} meaning",
            f'why {keyword}',
            f"how to {keyword}",
            f"{keyword} definition",
            f"best {keyword}",
            f"{keyword} recent",
            f"{keyword} latest news"
        ]

        return random.sample(base_queries, min(variations, len(base_queries)))
    
    def perform_search_operations(self, bot_id, keyword, search_engine='google', searches_per_bot=10, delay_range=(2, 8)):
        def search_worker():
            queries = self.generate_search_queries(keyword, searches_per_bot)
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36')

            try:
                driver = webdriver.Chrome(options=options)
                search_url = self.search_engines.get(search_engine, self.search_engines['google'])
                searches_performed = 0

                for query in queries:
                    try:
                        encoded_query = quote(query)
                        driver.get(f'{search_url}{encoded_query}')
                        searches_performed += 1

                        #Simulating human behaviour
                        driver.execute_script('window.scrollTo(0, document.body.scrollHeight/3);')
                        time.sleep(random.uniform(1, 3))

                        #Randomly click on results ( 30% chance)
                        if random.random() > 0.7:
                            results = driver.find_elements(By.CSS_SELECTOR, 'h3, a h3')
                            if results:
                                result_to_click = random.choice(results[:3])
                                driver.execute_script("argument[0].click();", result_to_click)
                                time.sleep(random.uniform(3, 8))
                                driver.back()
                                time.sleep(1)
                        time.sleep(random.uniform(delay_range[0], delay_range[1]))
                    except Exception as e:
                        logger.error(f'Search error for bot {bot_id}: {e}')
                        continue
                driver.quit()
                logger.info(f"Bot {bot_id} performed {searches_performed} searches for '{keyword}'")
                return { "status": "completed", "searches_performed": searches_performed}

            except Exception as e:
                logger.error(f"Browser error for bot {bot_id}: {e}")
                return { "status": "failed",  "error": str(e)}
        
        if bot_id not in self.search_sessions:
            thread = threading.Thread(target=search_worker)
            thread.start()
            self.search_sessions[bot_id] = {
                'thread': thread,
                'keyword': keyword,
                'started_at': time.time()
            }
            return { 'status': 'started', 'keyword': keyword, 'searches_planned': searches_per_bot}
        
        return { "status": 'already_running'}

    def start_trend_campaign(self, campaign_name, keyword, bots_count=10, duration_hours=24, searches_per_hour=5):
        def campaign_manager():
            start_time = time.time()
            end_time = start_time + (duration_hours * 3600)

            while time.time() < end_time and campaign_name in self.trend_operations:
                #getting available bot count (to query from database)
                available_bots = [f'bot_{i}' for i in range(1, bots_count + 1)]

                for bot_id in available_bots:
                    if bot_id not in self.search_sessions:
                        self.perform_search_operations(
                            bot_id, keyword, 
                            searches_per_bot=searches_per_hour,
                            delay_range=(5, 15)
                        )
                
                #Wait for next cycle
                time.sleep(3600) #wait for one hour

            if campaign_name in self.trend_operations:
                del self.trend_operations[campaign_name]
                logger.info(f"SEO campaign '{campaign_name}' completed")
        
        if campaign_name not in self.trend_operations:
            thread = threading.Thread(target=campaign_manager)
            thread.start()
            self.trend_operations[campaign_name] = {
                'thread': thread,
                'keyword': keyword,
                'started_at': time.time(),
                'duration': duration_hours
            }

            return { 'status': 'campaign_started', 'campaign': campaign_name}
        
        return { 'status': 'campaign_exists'}

    def stop_campaign(self, campaign_name):
        if campaign_name in self.trend_operations:
            del self.trend_operations[campaign_name]
            return { 'status': 'campaign_stopped', 'campaign': campaign_name}
        
        return { 'status': 'campaign_not_found'}

    def get_campaign_stats(self, campaign_name):
        if campaign_name in self.trend_operations:
            campaign = self.trend_operations[campaign_name]
            active_searches = len([s for s in self.search_sessions.values() if s.get('keyword') == campaign['keyword']])
            return {
                'campaign': campaign_name,
                'keyword': campaign['keyword'],
                'active_searches': active_searches,
                'running_time': time.time() - campaign['started_at'],
                'status': 'active'
            }
        return { 'status': 'campaign_not_found'}