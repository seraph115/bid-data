# Technical Architecture: Distributed Crawling

This document explains how the `bid_scraper` system achieves distributed crawling where multiple containers/nodes work together on a single data source.

## Core Principle: Shared Redis Queue

The system uses [Scrapy-Redis](https://github.com/rmax/scrapy-redis) to replace the default local scheduler of Scrapy with a Redis-based scheduler.

1. **Shared Request Queue**: Instead of keeping pending URLs in memory (RAM), all scrapers push new requests to a Redis list (`<spider_name>:requests`).
2. **Centralized Deduplication**: A Redis-based DupeFilter (`<spider_name>:dupefilter`) ensures that even if multiple nodes try to add the same URL, it is only added once.
3. **Atomic Operations**: Redis ensures that when a scraper "pops" a URL to process, no other scraper can get the same URL.

## How Multi-Container Scaling Works

When you run multiple containers (e.g., using `docker-compose up --scale bid_scraper=3`), the following happens:

1. **Startup**: All 3 containers start and connect to the **same** Redis server (defined by `REDIS_HOST`).
2. **Seeding**: All 3 containers execute `start_requests`.
    - They all generate the initial "Page 1" request.
    - Redis receives 3 identical requests.
    - The **DupeFilter** accepts the first one and discards the other two as duplicates.
    - Result: Only **one** "Page 1" request exists in the queue.
3. **Processing**:
    - **Container A** grabs "Page 1", downloads it, and parses it.
    - **Container A** finds links for "Page 2" and "Detail Page X", pushing them to Redis.
    - **Container B** and **Container C**, which were idle (or waiting), now see new tasks in Redis.
    - **Container B** might grab "Page 2".
    - **Container C** might grab "Detail Page X".

## Usage Guide

### 1. Same Source, Multiple Workers

To speed up collection of a single channel (e.g., `69311`):

```bash
# Start 3 workers sharing the workload
docker-compose up -d --scale bid_scraper=3
```

- **Configuration**: No change needed.
- **Effect**: Throughput increases ~3x (bottleneck becomes target site rate limit or network).

### 2. Multiple Sources, Multiple Workers

To scrape Channel A and Channel B simultaneously:

```bash
# Start default workers for Channel A (configured in docker-compose.yml)
docker-compose up -d

# Start an extra worker specifically for Channel B
docker-compose exec bid_scraper scrapy crawl jl_zfcg -a channel_id=69310
```

Alternatively, you can run different spider names if you had them.

## Data Consistency

- **MySQL**: Transactional database. Multiple scrapers can insert simultaneously. The `ON DUPLICATE KEY UPDATE` clause prevents errors if two scrapers process the same item (though DupeFilter usually prevents this upstream).
- **Files**: Stored in a Docker Volume (`./downloads` map). If scaling across **different machines**, you must ensure they either use a shared network file system (NFS/S3) or accept that files are scattered across nodes. Use `CustomFilesPipeline` to upload to S3 for true distributed file storage.
