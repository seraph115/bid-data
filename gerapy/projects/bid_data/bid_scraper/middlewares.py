# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class BidScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class BidScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


import requests
import logging

class RandomProxyMiddleware:
    def __init__(self, proxy_api_url):
        self.proxy_api_url = proxy_api_url
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_api_url=crawler.settings.get('PROXY_API_URL')
        )

    def process_request(self, request, spider):
        if not self.proxy_api_url:
            return None

        # Ignore if proxy is already set
        if 'proxy' in request.meta:
            return None

        try:
            # Simple implementation: Get 1 proxy per request
            # For high performance, you should maintain a local pool list
            response = requests.get(self.proxy_api_url, timeout=5)
            if response.status_code == 200:
                proxy = response.text.strip()
                if proxy:
                    if not proxy.startswith('http'):
                        proxy = f"http://{proxy}"
                    request.meta['proxy'] = proxy
                    self.logger.debug(f"Using Proxy: {proxy}")
        except Exception as e:
            self.logger.warning(f"Failed to get proxy: {e}")
            
    def process_exception(self, request, exception, spider):
        # Log failed proxy
        if 'proxy' in request.meta:
            self.logger.warning(f"Proxy failed: {request.meta['proxy']}, Exception: {exception}")
            # Retry request could be handled here or by Scrapy's RetryMiddleware
            

