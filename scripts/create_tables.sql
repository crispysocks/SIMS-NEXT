-- Student Information Management System Database Setup
-- This script creates the students table

CREATE DATABASE IF NOT EXISTS sims;
USE sims;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    age INT NOT NULL,
    native_place VARCHAR(100),
    class_id INT,
    enrollment_date DATE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_no (student_no),
    INDEX idx_class_id (class_id),
    INDEX idx_is_deleted (is_deleted),
    INDEX idx_class_id_deleted (class_id, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Teachers Table
CREATE TABLE IF NOT EXISTS teachers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    entry_date DATE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_teacher_no_deleted (teacher_no, is_deleted),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Classes Table
CREATE TABLE IF NOT EXISTS classes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    class_no VARCHAR(50) NOT NULL UNIQUE,
    class_name VARCHAR(100) NOT NULL,
    head_teacher_no VARCHAR(20) NOT NULL UNIQUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_class_no_deleted (class_no, is_deleted),
    INDEX idx_head_teacher_no_deleted (head_teacher_no, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scores Table
CREATE TABLE IF NOT EXISTS scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_no VARCHAR(20) NOT NULL COMMENT '学号',
    student_name VARCHAR(100) NOT NULL COMMENT '学生姓名（冗余）',
    exam_name VARCHAR(100) NOT NULL COMMENT '考试名称',
    score DECIMAL(5,2) NOT NULL COMMENT '成绩（>=0）',
    is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_student_no (student_no),
    INDEX idx_exam_name (exam_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT(1) DEFAULT 0,
    INDEX idx_username (username),
    INDEX idx_username_deleted (username, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- High Schools Table (升学预测模块)
CREATE TABLE IF NOT EXISTS high_schools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_name VARCHAR(100) NOT NULL,
    school_level VARCHAR(10) NOT NULL COMMENT 'L1, L2, L3, L4',
    region VARCHAR(50) NOT NULL,
    annual_admission_count INT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_school_name (school_name),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Admission Score Lines Table (升学预测模块)
CREATE TABLE IF NOT EXISTS admission_score_lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    year INT NOT NULL,
    admission_score INT NOT NULL,
    admission_rank INT NOT NULL,
    student_count INT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES high_schools(id),
    INDEX idx_school_year (school_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Score Rank Lines Table (升学预测模块)
CREATE TABLE IF NOT EXISTS score_rank_lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL,
    region VARCHAR(50) NOT NULL,
    score_min INT NOT NULL,
    score_max INT NOT NULL,
    rank_min INT NOT NULL,
    rank_max INT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    INDEX idx_year_region (year, region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Exam Records Table (升学预测模块)
CREATE TABLE IF NOT EXISTS exam_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    student_no VARCHAR(20) NOT NULL,
    exam_name VARCHAR(100) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    score INT NOT NULL,
    ranking INT COMMENT '单科排名',
    total_score INT COMMENT '本次考试总分',
    total_ranking INT COMMENT '本次考试总分排名',
    exam_time DATETIME NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    INDEX idx_student_no (student_no),
    INDEX idx_exam_time (exam_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Student Portraits Table (升学预测模块)
CREATE TABLE IF NOT EXISTS student_portraits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    overall_score FLOAT NOT NULL DEFAULT 0.0,
    subject_strengths TEXT COMMENT 'JSON - 优势学科',
    subject_weaknesses TEXT COMMENT 'JSON - 弱势学科',
    trend VARCHAR(20) COMMENT 'rising, stable, declining',
    risk_level VARCHAR(20) COMMENT 'low, medium, high',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Chat Sessions Table (升学预测模块)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    messages TEXT NOT NULL DEFAULT '[]',
    message_count INT DEFAULT 0,
    last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_id (student_id),
    INDEX idx_last_active (last_active_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Journey Conversation History
CREATE TABLE IF NOT EXISTS journey_conversation (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    personality VARCHAR(64),
    emotion VARCHAR(64),
    tone VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_journey_conv_session (session_id),
    INDEX idx_journey_conv_session_created (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Journey Game State
CREATE TABLE IF NOT EXISTS journey_state (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    user_role VARCHAR(64) DEFAULT '五徒弟',
    current_stage VARCHAR(32),
    progress INT DEFAULT 0,
    karma INT DEFAULT 0,
    companions JSON,
    chapter INT DEFAULT 1,
    level_id INT DEFAULT 1,
    stage_data JSON,
    knowledge_cards JSON,
    achievements JSON,
    cleared_chapters JSON,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_journey_state_session (session_id),
    INDEX idx_journey_state_session_active (session_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Journey Persona Corpus (Milvus data mirror for debugging)
CREATE TABLE IF NOT EXISTS journey_persona (
    id VARCHAR(64) PRIMARY KEY,
    chapter INT NOT NULL,
    speaker VARCHAR(64),
    embedding_text VARCHAR(4096),
    meta_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 导入种子数据
SOURCE scripts/seed_data.sql;
