USE bid_data;

-- Drop child tables first
DROP TABLE IF EXISTS parsed_notices;
DROP TABLE IF EXISTS parsed_data;
DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS bidding_info_attachments;
DROP TABLE IF EXISTS bid_attachments;

-- Drop parent tables
DROP TABLE IF EXISTS notices;
DROP TABLE IF EXISTS bidding_infos;
DROP TABLE IF EXISTS bid_records;

-- 1. Main Data Table
CREATE TABLE bid_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500),
    publish_date DATETIME,
    url VARCHAR(500) UNIQUE,
    content LONGTEXT,
    stage TINYINT COMMENT '1: 招标信息, 2: 中标公告',
    source_channel VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_publish_date (publish_date),
    INDEX idx_stage (stage)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Attachments Table
CREATE TABLE bid_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bid_record_id INT,
    file_url VARCHAR(1000),
    local_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bid_record_id) REFERENCES bid_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Unified Parsed Data Table (New)
CREATE TABLE parsed_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bid_record_id INT,
    project_name VARCHAR(500),
    project_code VARCHAR(100),
    purchaser VARCHAR(200),
    amount DECIMAL(20, 2),
    supplier VARCHAR(500),
    raw_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bid_record_id) REFERENCES bid_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
