import scrapy

class BidRecordItem(scrapy.Item):
    # Core fields (bid_records)
    title = scrapy.Field()
    publish_date = scrapy.Field()
    url = scrapy.Field()
    content = scrapy.Field()
    source_channel = scrapy.Field()
    stage = scrapy.Field() # 1: Bidding, 2: Winning
    
    # Attachments
    file_urls = scrapy.Field() # Used by built-in FilesPipeline
    files = scrapy.Field()     # Populated by FilesPipeline
