-- ============================================================
-- SmartLegal 数据库初始化脚本
-- 使用方法: mysql -u root -p < init.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_legal
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_legal;

-- ============================================================
-- 1. 用户与权限 (RBAC)
-- ============================================================

CREATE TABLE IF NOT EXISTS sys_user (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password      VARCHAR(255) NOT NULL,
    real_name     VARCHAR(50),
    email         VARCHAR(100),
    phone         VARCHAR(20),
    avatar        VARCHAR(255),
    status        TINYINT      DEFAULT 1,
    last_login_time DATETIME,
    create_time   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    update_time   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted       TINYINT      DEFAULT 0,
    INDEX idx_username (username)
) ENGINE=InnoDB COMMENT='系统用户';

CREATE TABLE IF NOT EXISTS sys_role (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_name     VARCHAR(50)  NOT NULL UNIQUE,
    role_code     VARCHAR(50)  NOT NULL UNIQUE,
    description   VARCHAR(200),
    status        TINYINT      DEFAULT 1,
    create_time   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    update_time   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='系统角色';

CREATE TABLE IF NOT EXISTS sys_user_role (
    id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    UNIQUE KEY uk_user_role (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES sys_role(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='用户-角色关联';

CREATE TABLE IF NOT EXISTS sys_permission (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    perm_name   VARCHAR(50)  NOT NULL,
    perm_code   VARCHAR(100) NOT NULL UNIQUE,
    perm_type   VARCHAR(20)  DEFAULT 'menu',
    parent_id   BIGINT       DEFAULT 0,
    path        VARCHAR(200),
    icon        VARCHAR(100),
    sort_order  INT          DEFAULT 0,
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='权限表';

CREATE TABLE IF NOT EXISTS sys_role_permission (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_id       BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    UNIQUE KEY uk_role_perm (role_id, permission_id),
    FOREIGN KEY (role_id)       REFERENCES sys_role(id)       ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES sys_permission(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='角色-权限关联';

CREATE TABLE IF NOT EXISTS sys_notification (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT       NOT NULL,
    title       VARCHAR(200) NOT NULL,
    content     TEXT,
    type        VARCHAR(50),
    related_id  BIGINT,
    is_read     TINYINT      DEFAULT 0,
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    INDEX idx_user_read (user_id, is_read)
) ENGINE=InnoDB COMMENT='系统通知';

-- ============================================================
-- 2. 智能审查
-- ============================================================

CREATE TABLE IF NOT EXISTS review_record (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT       NOT NULL,
    file_name       VARCHAR(255),
    content_text    LONGTEXT,
    status          VARCHAR(20)  DEFAULT 'pending',
    total_risks     INT          DEFAULT 0,
    critical_risks  INT          DEFAULT 0,
    general_risks   INT          DEFAULT 0,
    low_risks       INT          DEFAULT 0,
    review_summary  TEXT,
    ai_model        VARCHAR(50),
    processing_time INT,
    create_time     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES sys_user(id),
    INDEX idx_user_review (user_id, create_time)
) ENGINE=InnoDB COMMENT='审查记录';

CREATE TABLE IF NOT EXISTS review_risk (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    review_id        BIGINT       NOT NULL,
    risk_level       VARCHAR(20)  NOT NULL,
    risk_category    VARCHAR(50),
    risk_title       VARCHAR(200) NOT NULL,
    risk_description TEXT,
    risk_position    TEXT,
    clause_section   VARCHAR(100),
    suggestion       TEXT,
    suggested_text   TEXT,
    legal_basis      TEXT,
    create_time      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES review_record(id) ON DELETE CASCADE,
    INDEX idx_review_level (review_id, risk_level)
) ENGINE=InnoDB COMMENT='审查风险明细';

-- ============================================================
-- 3. 合同生成
-- ============================================================

CREATE TABLE IF NOT EXISTS generation_record (
    id                   BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id              BIGINT       NOT NULL,
    session_id           VARCHAR(100) NOT NULL,
    contract_type        VARCHAR(50),
    conversation_history JSON,
    generated_content    LONGTEXT,
    status               VARCHAR(20)  DEFAULT 'draft',
    create_time          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    update_time          DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES sys_user(id),
    INDEX idx_user_session (user_id, session_id)
) ENGINE=InnoDB COMMENT='合同生成记录';

-- ============================================================
-- 4. 合同比对
-- ============================================================

CREATE TABLE IF NOT EXISTS compare_record (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id          BIGINT NOT NULL,
    contract_a_id    BIGINT,
    contract_b_id    BIGINT,
    similarity_score DECIMAL(5,2),
    total_diffs      INT    DEFAULT 0,
    additions        INT    DEFAULT 0,
    deletions        INT    DEFAULT 0,
    modifications    INT    DEFAULT 0,
    create_time      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES sys_user(id),
    INDEX idx_user_compare (user_id, create_time)
) ENGINE=InnoDB COMMENT='合同比对记录';

CREATE TABLE IF NOT EXISTS compare_diff (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    compare_id      BIGINT NOT NULL,
    diff_type       VARCHAR(20) NOT NULL,
    contract_a_text TEXT,
    contract_b_text TEXT,
    clause_section  VARCHAR(100),
    summary         VARCHAR(500),
    FOREIGN KEY (compare_id) REFERENCES compare_record(id) ON DELETE CASCADE,
    INDEX idx_compare_type (compare_id, diff_type)
) ENGINE=InnoDB COMMENT='比对差异明细';

-- ============================================================
-- 5. 知识库
-- ============================================================

CREATE TABLE IF NOT EXISTS kb_document (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(300) NOT NULL,
    content     LONGTEXT     NOT NULL,
    category    VARCHAR(100),
    tags        VARCHAR(500),
    source      VARCHAR(300),
    vector_id   VARCHAR(100),
    chunk_count INT          DEFAULT 0,
    status      TINYINT      DEFAULT 1,
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_kb_category (category)
) ENGINE=InnoDB COMMENT='知识库文档';

-- 合规检查记录表
CREATE TABLE compliance_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    file_name VARCHAR(255),
    content_text LONGTEXT,
    compliance_standard VARCHAR(100),
    industry VARCHAR(100),
    jurisdiction VARCHAR(100),
    overall_compliance VARCHAR(50),
    summary TEXT,
    total_issues INT DEFAULT 0,
    critical_issues INT DEFAULT 0,
    general_issues INT DEFAULT 0,
    low_issues INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PROCESSING',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES sys_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 合规问题详情表
CREATE TABLE compliance_issue (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_id BIGINT NOT NULL,
    issue_title VARCHAR(255),
    severity VARCHAR(20),
    clause_reference VARCHAR(255),
    description TEXT,
    legal_reference VARCHAR(500),
    recommendation TEXT,
    penalty_risk VARCHAR(255),
    INDEX idx_record_id (record_id),
    FOREIGN KEY (record_id) REFERENCES compliance_record(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 6. 初始数据
-- ============================================================

-- 角色
INSERT INTO sys_role (role_name, role_code, description) VALUES
('管理员',   'ROLE_ADMIN', '系统管理员'),
('普通用户', 'ROLE_USER',  '普通用户');

-- 用户 (密码 123456, BCrypt)
INSERT INTO sys_user (username, password, real_name, email) VALUES
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '管理员',   'admin@smartlegal.com'),
('user',  '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '测试用户', 'user@smartlegal.com');

-- 角色分配
INSERT INTO sys_user_role (user_id, role_id) VALUES (1, 1), (2, 2);

-- 权限
INSERT INTO sys_permission (id, perm_name, perm_code, perm_type, parent_id, path, icon, sort_order) VALUES
(1,  '工作台',     'dashboard',        'menu', 0, '/dashboard',      'Odometer',   1),
(2,  '智能审查',   'review:manage',    'menu', 0, '/review',         'Warning',    2),
(3,  '合同生成',   'generate:manage',  'menu', 0, '/generate',       'Edit',       3),
(4,  '合同比对',   'compare:manage',   'menu', 0, '/compare',        'Switch',     4),
(5,  '合规检查',   'compliance:manage','menu', 0, '/compliance',     'Shield',     5),
(6,  '知识库',     'knowledge:manage', 'menu', 0, '/knowledge',      'Reading',    6),
(7,  '通知中心',   'notification:view','menu', 0, '/notifications',  'Bell',       7);

-- 管理员拥有所有权限
INSERT INTO sys_role_permission (role_id, permission_id) VALUES (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7);
INSERT INTO sys_role_permission (role_id, permission_id) VALUES (2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(2,7);
