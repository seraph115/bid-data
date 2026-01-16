BOT_NAME = 'bid_scraper'

SPIDER_MODULES = ['bid_scraper.spiders']
NEWSPIDER_MODULE = 'bid_scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

import os

# Scrapy-Redis Configuration
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER_PERSIST = True # Don't clear Redis queue on finish

# Redis Connection
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = 6379

# Item Pipelines
ITEM_PIPELINES = {
    'bid_scraper.pipelines.CustomFilesPipeline': 1,
    'bid_scraper.pipelines.MysqlPipeline': 300,
    # 'scrapy_redis.pipelines.RedisPipeline': 400, # Optional: store items in Redis
}

# Files Store
FILES_STORE = '/app/downloads'
MEDIA_ALLOW_REDIRECTS = True

# MySQL Config
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': 'root',
    'password': 'root', # Matches docker-compose
    'database': 'bid_data'
}

# Request settings
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Proxy Configuration
PROXY_API_URL = os.getenv('PROXY_API_URL', '')  # e.g., http://proxypool:5555/random
PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'

DOWNLOADER_MIDDLEWARES = {
    'bid_scraper.middlewares.RandomProxyMiddleware': 100,
    'bid_scraper.middlewares.BidScraperDownloaderMiddleware': 543,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
