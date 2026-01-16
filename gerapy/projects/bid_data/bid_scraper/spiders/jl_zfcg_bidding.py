import scrapy
import json
import re
import redis
import os
from scrapy import signals
from bid_scraper.items import BidRecordItem
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity

class JlZfcgBiddingSpider(scrapy.Spider):
    name = "jl_zfcg_bidding"
    channel_id = '69308'
    
    # Singleton Config
    LOCK_KEY = "spider:lock:jl_zfcg_bidding"
    LOCK_EXPIRE = 3600
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(JlZfcgBiddingSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        # Init Redis
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_conn = redis.Redis(host=redis_host, port=6379, decode_responses=True)
        
        # Try Lock
        is_locked = self.redis_conn.set(self.LOCK_KEY, "locked", nx=True, ex=self.LOCK_EXPIRE)
        if not is_locked:
            self.logger.warning(f"Singleton Lock Exists for {self.name}. Stopping job.")
            self.crawler.engine.close_spider(self, 'duplicate_run_prevented')
            self.has_lock = False
        else:
            self.logger.info(f"Singleton Lock Acquired for {self.name}")
            self.has_lock = True

    def spider_closed(self, spider):
        if hasattr(self, 'has_lock') and self.has_lock:
            self.redis_conn.delete(self.LOCK_KEY)
            self.logger.info(f"Singleton Lock Released for {self.name}")

    def start_requests(self):
        url = "https://haiyun.jl.gov.cn/irs/front/search"
        payload = {
            "code": "1892dd01822",
            "searchWord": None,
            "orderBy": "time",
            "dataTypeId": "501",
            "searchBy": "all",
            "pageNo": 1,
            "pageSize": 10,
            "granularity": "ALL",
            "isSearchForced": 0,
            "customFilter": {
                "operator": "and",
                "properties": [{"property": "channel_id", "operator": "eq", "value": self.channel_id, "weight": 100}]
            }
        }
        
        yield scrapy.Request(
            url, 
            method="POST", 
            body=json.dumps(payload), 
            headers={'Content-Type':'application/json'}, 
            callback=self.parse_list, 
            meta={'payload': payload},
            dont_filter=True
        )

    def parse_list(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON response")
            return

        # Parse items
        items = data.get('data', {}).get('middle', {}).get('listAndBox', [])
        for item in items:
            if item.get('type') == 'DATA':
                d = item.get('data', {})
                url = d.get('url')
                if url:
                    meta = {
                        'title': self.clean_title(d.get('title')),
                        'publish_date': d.get('time'),
                        'url': url
                    }
                    yield scrapy.Request(url, callback=self.parse_detail, meta=meta)

        # Pagination
        pager = data.get('data', {}).get('pager', {})
        current_page = pager.get('pageNo')
        total_page = pager.get('pageCount')
        
        self.logger.info(f"Pagination Debug: Current Page: {current_page}, Total Pages: {total_page}")

        if current_page and total_page and current_page < total_page:
            next_page = current_page + 1
            # Deep copy payload to ensure safety
            import copy
            payload = copy.deepcopy(response.meta['payload'])
            payload['pageNo'] = next_page
            
            self.logger.info(f"Yielding Next Page: {next_page}")
            
            yield scrapy.Request(
                response.url, 
                method="POST", 
                body=json.dumps(payload), 
                headers={'Content-Type':'application/json'}, 
                callback=self.parse_list, 
                meta={'payload': payload},
                dont_filter=True
            )

    def parse_detail(self, response):
        loader = ItemLoader(item=BidRecordItem(), response=response)
        loader.default_output_processor = TakeFirst()
        loader.file_urls_out = Identity()
        loader.files_out = Identity()
        
        loader.add_value('url', response.meta.get('url'))
        loader.add_value('title', response.meta.get('title'))
        loader.add_value('publish_date', response.meta.get('publish_date')) 
        loader.add_value('source_channel', 'zfcg_bid')
        loader.add_value('stage', 1) # Bidding Information
        
        content_html = response.css('#detailCnt').get()
        if content_html:
            loader.add_value('content', content_html)
        else:
            self.logger.warning(f"No content found for {response.url}")
        
        file_urls = []
        links = response.css('#detailCnt a::attr(href)').getall()
        for link in links:
            full_link = response.urljoin(link)
            if re.search(r'\.(pdf|doc|docx|xls|xlsx|zip|rar)$', full_link, re.I) or 'cmd=download' in full_link:
                file_urls.append(full_link)
        
        if file_urls:
            loader.add_value('file_urls', file_urls)
            
        yield loader.load_item()

    def clean_title(self, title):
        if not title:
            return ""
        return re.sub(r'<[^>]+>', '', title)
