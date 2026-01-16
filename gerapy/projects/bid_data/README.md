# 招标数据分布式采集系统 (Bid Data Distributed Scraper)

基于 Scrapy-Redis 的分布式爬虫系统，目前用于采集某省公共资源交易信息（政府采购）。

## 功能特性

- **分布式采集**: 使用 Redis 进行 URL 统一调度和去重。
- **数据持久化**: 数据存储在 MySQL (UTF8MB4)，附件文件下载到本地。
- **Docker 化部署**: 提供 MySQL、Redis 和 Scrapy 的一键启动环境。
- **UI 管理界面**: 集成 Gerapy 和 Scrapyd，提供可视化的爬虫管理、部署和调度功能。
- **独立爬虫设计**: 拆分为 `jl_zfcg_winning` (中标公告) 和 `jl_zfcg_bidding` (招标信息) 两个独立爬虫，互不干扰。
- **单例运行保护**: 内置 Redis 分布式锁，防止同一爬虫在上一周期未结束时重复运行。
- **LLM 集成**: 包含用于批量解析 HTML 内容的 Ollama 集成脚本。

## 附录: 爬虫对照表

所有数据现已通过 `stage` 字段区分，统一存储在 `bid_records` 表中。

| 爬虫名称 | 对应栏目 | Channel ID | stage 值 | 存储表 |
| :--- | :--- | :--- | :--- | :--- |
| **`jl_zfcg_winning`** | 中标公告 | 69311 | `2` | `bid_records` |
| **`jl_zfcg_bidding`** | 招标信息 | 69308 | `1` | `bid_records` |

## 环境要求

- Docker
- Docker Compose

## 快速开始

### 1. 启动服务(含管理界面)

运行以下命令将在通过 Docker 启动 MySQL、Redis、Scrapyd (爬虫节点) 和 Gerapy (管理界面)：

```bash
docker-compose up -d
```

### 2. 访问管理界面

- **Gerapy 控制台**: [http://localhost:8000](http://localhost:8000)
  - 默认账号: `admin`
  - 默认密码: `admin`
- **Scrapyd 状态页**: [http://localhost:6800](http://localhost:6800)

### 3. 初始化配置 (由 Web 界面完成)

1. **登录 Gerapy**：使用 `admin/admin` 登录。
2. **添加主机 (Client)**：
    - 点击左侧「主机管理」->「创建」。
    - 名称: `Scrapyd-01`
    - IP: `scrapyd`
    - 端口: `6800`
    - 点击「创建」，确认状态为**正常**。
3. **部署项目**：
    - 点击左侧「项目管理」。
    - 点击右侧的 **「部署」** 按钮 -> **「打包并部署」**。
    - *注意：若需重新部署更新后的代码，请先在界面上删除旧打包文件或直接覆盖部署。*

### 4. 执行采集任务与查看日志

1. **运行任务**:
    - 点击左侧「任务管理」->「创建任务」。
    - 填写名称，选择爬虫 (`jl_zfcg_winning` 或 `jl_zfcg_bidding`)。
    - 触发方式选择 `Interval` (例如每 10 分钟)。
    - 保存后，点击右侧的 **「状态」** (Monitor) 按钮。
    - 在弹出的调度列表页面，点击右上角的 **「运行」** (Run) 按钮即可立即触发。

2. **查看日志**:
    - 在上述的 **「状态」** (Monitor) 页面下方，会列出所有运行记录 (Reports)。
    - 点击 **「Log」** 列的链接，即可直接查看详细运行日志。
    - 也可以访问 Scrapyd 原生界面查看: [http://localhost:6800/jobs](http://localhost:6800/jobs)。

---

### (可选) 命令行方式仍可使用

虽然有了界面，你依然可以使用命令行在容器内直接调度（适合调试）：

#### 采集【中标公告】

```bash
docker-compose exec scrapyd scrapy crawl jl_zfcg_winning
```

#### 采集【招标信息】

```bash
docker-compose exec scrapyd scrapy crawl jl_zfcg_bidding
```

### 5. 服务管理

- **查看服务状态**:

  ```bash
  docker-compose ps
  ```

- **查看实时日志**:

  ```bash
  docker-compose logs -f scrapyd gerapy
  ```

- **重启爬虫服务**:

  ```bash
  docker-compose restart scrapyd
  ```

- **停止所有服务**:

  ```bash
  docker-compose down
  ```

## 数据库连接

MySQL 容器已映射到宿主机的 **3307** 端口，以避免与通过本地 MySQL 冲突。

- **主机**: `localhost`
- **端口**: `3307`
- **用户名**: `root`
- **密码**: `root`
- **数据库**: `bid_data`

### JDBC 连接字符串

```text
jdbc:mysql://localhost:3307/bid_data?useUnicode=true&characterEncoding=utf8mb4&serverTimezone=Asia/Shanghai
```

## 项目结构

- `bid_scraper/`: Scrapy 爬虫项目源码。
- `docker-compose.yml`: Docker 编排文件，定义了服务依赖和启动命令。
- `Dockerfile`: Python 运行环境定义。
- `schema.sql`: 数据库初始化脚本。
- `llm_processor.py`: LLM 数据解析脚本。
- `gerapy/`: Gerapy 数据存储目录。
- `gerapy/`: Gerapy 数据存储目录。
- `scrapyd.conf`: Scrapyd 配置文件。

## 反爬策略配置 (Anti-Crawling)

系统已内置反爬策略，如需启用代理 IP 池，请在 `docker-compose.yml` 中配置环境变量：

```yaml
  scrapyd:
    environment:
      - PROXY_API_URL=http://your-proxy-pool-api/get  # 设置代理获取地址
      - PROXY_ENABLED=true  # 设置为 true 开启代理，默认 false 关闭
```

- **随机延迟**: 默认开启 2 秒随机延迟。
- **IP 代理**: 也就是资源池功能。需配置 `PROXY_ENABLED=true` 才会生效。
