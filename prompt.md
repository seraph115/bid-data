# User Prompts & Project Evolution Log

This document records the key prompts and requirements provided by the user during the development of the Bid Data Distributed Scraper.

## Phase 1: Project Initialization & Core Scraper
>
> "Create a distributed crawler system using Scrapy-Redis to scrape Jilin Public Resource Trading Center."
> "Need to scrape 'Winning Announcements' (Channel 69311) and store in MySQL."
> "Analyze the JSON API for list pages and implement pagination."

## Phase 2: Infrastructure & Docker
>
> "Dockerize the environment. Need MySQL, Redis, and the Scraper in docker-compose."
> "Ensure MySQL uses utf8mb4 and persistent storage."

## Phase 3: Expansion & LLM Integration
>
> "Integrate Ollama for parsing HTML content using LLM."
> "Add a new source: 'Bidding Information' (Channel 69308)."
> "Modify schema to support the new data type."

## Phase 4: UI & Management
>
> "Add Gerapy and Scrapyd for web-based task management."
> "Fix connection issues between Gerapy and Scrapyd in Docker."
> "Refactor code to separate 'Winning' and 'Bidding' into two distinct independent spiders."

## Phase 5: Refactoring & Optimization
>
> "Refactor database: Merge `notices` and `bidding_infos` into a single `bid_records` table, distinguished by a `stage` column."
> "Fix issue where Gerapy projects are empty/invisible."

## Phase 6: Advanced Features (Stability & Anti-Crawling)
>
> "Implement Singleton pattern: Prevent new tasks from starting if the previous one is still running (Overlapping Schedule)."
> "Add Anti-Crawling strategies: Random download delay and IP Proxy pool integration."
> "Push the final project code to GitHub."
