-- =============================================
-- 智能会议纪要助手系统 - 数据库初始化脚本
-- 版本: V2.0 (企业多用户版)
-- 数据库: MySQL 8.0
-- 字符集: utf8mb4
-- =============================================

-- 创建数据库
DROP DATABASE IF EXISTS db_meeting_minutes;
CREATE DATABASE db_meeting_minutes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_meeting_minutes;

-- =============================================
-- 1. 部门表 (t_dept)
-- =============================================
CREATE TABLE t_dept (
    dept_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '部门ID',
    dept_name VARCHAR(100) NOT NULL UNIQUE COMMENT '部门名称（唯一）',
    dept_desc VARCHAR(500) DEFAULT NULL COMMENT '部门描述',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_dept_name (dept_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- =============================================
-- 2. 用户表 (t_user)
-- =============================================
CREATE TABLE t_user (
    user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（登录名，唯一）',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
    nickname VARCHAR(100) DEFAULT NULL COMMENT '昵称',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    avatar_url VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    role ENUM('super_admin', 'normal_user') NOT NULL DEFAULT 'normal_user' COMMENT '角色：super_admin=超级管理员, normal_user=普通用户',
    dept_id INT DEFAULT NULL COMMENT '所属部门ID',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '账号状态：1=启用, 0=禁用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (dept_id) REFERENCES t_dept(dept_id) ON DELETE SET NULL,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_dept_id (dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- =============================================
-- 3. 会议表 (t_meeting)
-- =============================================
CREATE TABLE t_meeting (
    meeting_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '会议ID',
    title VARCHAR(200) NOT NULL COMMENT '会议标题',
    file_path VARCHAR(500) NOT NULL COMMENT '音视频文件本地路径',
    file_url VARCHAR(500) NOT NULL COMMENT '音视频文件公网访问URL',
    duration INT DEFAULT NULL COMMENT '音频时长（秒）',
    status ENUM('uploaded', 'transcribing', 'transcribed', 'summarizing', 'done', 'failed') NOT NULL DEFAULT 'uploaded' COMMENT '会议状态',
    error_msg TEXT DEFAULT NULL COMMENT '错误信息（失败时记录）',
    asr_task_id VARCHAR(100) DEFAULT NULL COMMENT 'ASR任务ID',
    create_user_id INT NOT NULL COMMENT '创建人ID',
    share_dept TINYINT(1) NOT NULL DEFAULT 0 COMMENT '部门内分享：1=开启, 0=关闭',
    auto_process TINYINT(1) NOT NULL DEFAULT 1 COMMENT '自动处理：1=上传后自动处理, 0=手动触发',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (create_user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    INDEX idx_create_user_id (create_user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议表';

-- =============================================
-- 4. 转写句子表 (t_transcript)
-- =============================================
CREATE TABLE t_transcript (
    transcript_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '转写句子ID',
    meeting_id INT NOT NULL COMMENT '所属会议ID',
    speaker_id VARCHAR(50) NOT NULL COMMENT '说话人ID（如spk0, spk1）',
    sentence_index INT NOT NULL COMMENT '句子序号',
    start_time INT NOT NULL COMMENT '开始时间（毫秒）',
    end_time INT NOT NULL COMMENT '结束时间（毫秒）',
    content TEXT NOT NULL COMMENT '转写文本内容',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (meeting_id) REFERENCES t_meeting(meeting_id) ON DELETE CASCADE,
    INDEX idx_meeting_id (meeting_id),
    INDEX idx_speaker_id (speaker_id),
    INDEX idx_sentence_index (sentence_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='转写句子表';

-- =============================================
-- 5. 发言人表 (t_speaker)
-- =============================================
CREATE TABLE t_speaker (
    speaker_pk INT AUTO_INCREMENT PRIMARY KEY COMMENT '发言人主键',
    meeting_id INT NOT NULL COMMENT '所属会议ID',
    speaker_id VARCHAR(50) NOT NULL COMMENT '原始说话人ID',
    speaker_name VARCHAR(100) NOT NULL COMMENT '发言人显示名称（可编辑）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (meeting_id) REFERENCES t_meeting(meeting_id) ON DELETE CASCADE,
    UNIQUE KEY uk_meeting_speaker (meeting_id, speaker_id),
    INDEX idx_meeting_id (meeting_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发言人表';

-- =============================================
-- 6. 会议纪要表 (t_minutes)
-- =============================================
CREATE TABLE t_minutes (
    minutes_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '纪要ID',
    meeting_id INT NOT NULL UNIQUE COMMENT '所属会议ID（一对一）',
    summary TEXT DEFAULT NULL COMMENT '会议摘要',
    keywords VARCHAR(500) DEFAULT NULL COMMENT '关键词（逗号分隔）',
    todos JSON DEFAULT NULL COMMENT '待办事项JSON数组：[{content, owner, deadline}]',
    speaker_summary JSON DEFAULT NULL COMMENT '发言人总结JSON：{speaker_id: "总结内容"}',
    markdown LONGTEXT DEFAULT NULL COMMENT '完整Markdown格式纪要',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (meeting_id) REFERENCES t_meeting(meeting_id) ON DELETE CASCADE,
    INDEX idx_meeting_id (meeting_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议纪要表';

-- =============================================
-- 初始化数据
-- =============================================

-- 插入默认部门（用于测试和MVP阶段）
INSERT INTO t_dept (dept_name, dept_desc) VALUES
('技术部', '技术研发部门'),
('产品部', '产品管理部门'),
('运营部', '运营推广部门');

-- 插入超级管理员账号（初始密码：Admin@123456）
-- 密码哈希由 bcrypt.hashpw(b'Admin@123456', bcrypt.gensalt(rounds=12)) 生成
INSERT INTO t_user (username, password_hash, nickname, role, dept_id, is_active) VALUES
('admin', '$2b$12$Z.Hw3smcFVeylkd3su3bL.8HHQQUSUGlz16hXBOOPOTq1aKrzHQze', '系统管理员', 'super_admin', 1, 1);

-- 生产环境首次登录后必须修改初始密码

-- =============================================
-- 完成
-- =============================================
SELECT '数据库初始化完成！' AS message;
SELECT '默认超级管理员账号：admin，密码：Admin@123456（请在生产环境中修改）' AS notice;
