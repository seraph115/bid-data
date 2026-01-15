import mysql.connector
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.project import get_project_settings
import json
import os

class BidScraperPipeline:
    def process_item(self, item, spider):
        return item

class MysqlPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.db_config = settings.get('MYSQL_CONFIG')
        self.conn = None
        self.cursor = None

    def open_spider(self, spider):
        self.conn = mysql.connector.connect(charset='utf8mb4', **self.db_config)
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        from bid_scraper.items import BidRecordItem
        
        try:
            if isinstance(item, BidRecordItem):
                self._process_bid_record(item)
        except mysql.connector.Error as err:
            spider.logger.error(f"MySQL Error: {err}")
            
        return item

    def _process_bid_record(self, item):
        # Insert Main Record
        sql_record = """
            INSERT INTO bid_records (title, publish_date, content, url, source_channel, stage)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                title=VALUES(title), 
                content=VALUES(content),
                stage=VALUES(stage)
        """
        self.cursor.execute(sql_record, (
            item.get('title'),
            item.get('publish_date'),
            item.get('content'),
            item.get('url'),
            item.get('source_channel'),
            item.get('stage')
        ))
        self.conn.commit()
        record_id = self.cursor.lastrowid
        
        # Insert Attachments
        if item.get('files'):
            for f in item.get('files'):
                sql_file = """
                    INSERT INTO bid_attachments (bid_record_id, file_url, local_path)
                    VALUES (%s, %s, %s)
                """
                self.cursor.execute(sql_file, (
                    record_id,
                    f['url'],
                    f['path']
                ))
            self.conn.commit()

class CustomFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        # Hash text is default, can customize if needed
        return super().file_path(request, response, info, item=item)
