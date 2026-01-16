# 🐛 Bug Fixes Log (2026-01-16)

本次调试共修复了两个导致采集任务甚至无法启动或数据丢失的核心 Bug。

## 1. 采集任务瞬间结束 (Pagination Bug)

**问题现象**

- 启动爬虫后，仅抓取了第一页或前几页就立即停止 (`Closing spider (finished)`).
- 日志中出现大量 `Filtered duplicate request ...`。

**根本原因**

- `Scrapy-Redis` 的去重机制默认是开启的 (`DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"`).
- 爬虫在翻页时 (`parse_list` 方法)，生成的下一页 Request 没有设置禁用过滤。
- 如果这些列表页 URL 在之前的运行中已经被访问过（Redis 中有记录），Scrapy 就会认为它们是重复请求而直接丢弃，导致翻页链条断裂。

**修复方案**

- **涉及文件**:
  - `bid_scraper/spiders/jl_zfcg_bidding.py`
  - `bid_scraper/spiders/jl_zfcg_winning.py`
- **代码变更**:
    在生成翻页请求 (`yield scrapy.Request`) 时，显式添加 `dont_filter=True` 参数。

    ```python
    yield scrapy.Request(
        response.url, 
        method="POST", 
        body=json.dumps(payload), 
        # ...
        dont_filter=True  # <--- 强制不过滤，确保每次都重新抓取列表页
    )
    ```

---

## 2. 数据入库报错 (MySQL Foreign Key Error)

**问题现象**

- 爬虫日志中出现大量 MySQL 错误：
  `MySQL Error: 1452 (23000): Cannot add or update a child row: a foreign key constraint fails ...`
- `bid_records` 表有数据，但 `bid_attachments` 表数据缺失或部分丢失。

**根本原因**

- `BidRecordItem` 入库时使用了 `INSERT ... ON DUPLICATE KEY UPDATE` 语句。
- 在使用 `mysql-connector-python` 驱动连接 MySQL 时，如果 `UPDATE` 语句执行后并没有实际改变行内容（或者只是更新了时间戳等），`cursor.lastrowid` 有时会返回 `0` 或 `None`（取决于具体驱动版本和 MySQL 配置）。
- 由于 `record_id` 获取为 0，后续插入附件表 (`bid_attachments`) 时，外键 `bid_record_id` 指向了 0，导致违反外键约束（MySQL 中没有 id=0 的记录）。

**修复方案**

- **涉及文件**:
  - `bid_scraper/pipelines.py`
- **代码变更**:
    在 `MysqlPipeline` 中增加兜底逻辑：如果 `lastrowid` 为空或 0，则立即通过唯一的 `url` 反查数据库获取正确的 ID。

    ```python
    record_id = self.cursor.lastrowid
    
    # 修复逻辑：如果 record_id 为空 (说明是更新且 lastrowid 未返回)，则手动查询
    if not record_id:
        self.cursor.execute("SELECT id FROM bid_records WHERE url = %s", (item.get('url'),))
        result = self.cursor.fetchone()
        if result:
            record_id = result[0]
    ```

---

**验证结果**

- 修复后进行测试，爬虫成功翻页至第 20 页（测试限制）。
- 附件表 `bid_attachments` 数据量正常增长，未再出现外键报错。
