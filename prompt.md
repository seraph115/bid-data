# 用户提示词与项目演进日志 (User Prompts & Project Evolution Log)

本文档记录了招标数据分布式采集系统 (Bid Data Distributed Scraper) 开发过程中的关键用户需求与提示词。

## 第一阶段：项目初始化与核心爬虫
>
> "使用 Scrapy-Redis 创建一个分布式爬虫系统，用于采集吉林省公共资源交易中心数据。"
> "需要采集 '中标公告' (栏目号 69311) 并存储到 MySQL 中。"
> "分析列表页的 JSON API 接口并实现分页采集。"

## 第二阶段：基础设施与 Docker 化
>
> "将开发环境 Docker 化。需要在 docker-compose 中包含 MySQL, Redis 和爬虫服务。"
> "确保 MySQL 使用 utf8mb4 编码并配置持久化存储。"

## 第三阶段：功能扩展与 LLM 集成
>
> "集成 Ollama，利用 LLM 来解析 HTML 内容。"
> "增加一个新的采集源：'招标信息' (栏目号 69308)。"
> "修改数据库结构以支持新的数据类型。"

## 第四阶段：UI 与管理界面
>
> "引入 Gerapy 和 Scrapyd 以实现基于 Web 的任务管理。"
> "解决 Docker 环境下 Gerapy 与 Scrapyd 的连接问题。"
> "重构代码，将 '中标公告' 和 '招标信息' 拆分为两个独立的爬虫。"

## 第五阶段：重构与优化
>
> "重构数据库：将 `notices` 和 `bidding_infos` 合并为一张 `bid_records` 表，通过 `stage` 字段区分。"
> "修复 Gerapy 项目列表为空/不可见的问题。"

## 第六阶段：高级特性 (稳定性与反爬)
>
> "实现单例模式 (Singleton)：防止上一个任务未结束时新任务重复启动 (重叠调度保护)。"
> "添加反爬策略：实现随机下载延迟 (Random Delay) 和 IP 代理池 (Proxy Pool) 集成。"
> "将最终的项目代码推送到 GitHub。"
