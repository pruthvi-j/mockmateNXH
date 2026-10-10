-- =====================================================================
-- NextHire: Intelligent Mock Interview System
-- Database Schema for MySQL 8.x
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `nexthire_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `nexthire_db`;

-- Table 1: Users
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 2: Resumes
CREATE TABLE IF NOT EXISTS `resumes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `filename` VARCHAR(255) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,
    `extracted_text` LONGTEXT,
    `extracted_skills` JSON,
    `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_resumes_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 3: Question Bank
CREATE TABLE IF NOT EXISTS `question_bank` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `question_code` VARCHAR(20) NOT NULL UNIQUE, -- e.g. PL001
    `target_role` VARCHAR(100) NOT NULL,
    `category` VARCHAR(100) NOT NULL,
    `difficulty` ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
    `question_text` TEXT NOT NULL,
    `reference_answer` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_qb_role` (`target_role`),
    INDEX `idx_qb_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 4: Question Concepts
CREATE TABLE IF NOT EXISTS `question_concepts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `question_id` INT NOT NULL,
    `concept_keyword` VARCHAR(100) NOT NULL,
    `importance_weight` DECIMAL(3,2) DEFAULT 1.00,
    FOREIGN KEY (`question_id`) REFERENCES `question_bank`(`id`) ON DELETE CASCADE,
    INDEX `idx_qc_question` (`question_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 5: Interview Sessions (Isolation core)
CREATE TABLE IF NOT EXISTS `interview_sessions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_code` VARCHAR(64) NOT NULL UNIQUE, -- Unique Session UUID / Token
    `user_id` INT NOT NULL,
    `target_role` VARCHAR(100) NOT NULL,
    `status` ENUM('in_progress', 'completed', 'aborted') DEFAULT 'in_progress',
    `total_questions` INT DEFAULT 0,
    `answered_count` INT DEFAULT 0,
    `skipped_count` INT DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `completed_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_session_user` (`user_id`),
    INDEX `idx_session_code` (`session_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 6: Interview Questions (Assigned to a specific interview session)
CREATE TABLE IF NOT EXISTS `interview_questions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` INT NOT NULL,
    `question_id` INT NOT NULL,
    `order_index` INT NOT NULL,
    `status` ENUM('pending', 'answered', 'skipped') DEFAULT 'pending',
    FOREIGN KEY (`session_id`) REFERENCES `interview_sessions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`question_id`) REFERENCES `question_bank`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `uniq_session_question` (`session_id`, `question_id`),
    INDEX `idx_iq_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 7: User Answers
CREATE TABLE IF NOT EXISTS `user_answers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` INT NOT NULL,
    `question_id` INT NOT NULL,
    `transcript_text` TEXT,
    `audio_path` VARCHAR(500) NULL,
    `duration_seconds` INT DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `interview_sessions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`question_id`) REFERENCES `question_bank`(`id`) ON DELETE CASCADE,
    INDEX `idx_ua_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 8: Evaluation Results
CREATE TABLE IF NOT EXISTS `evaluation_results` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` INT NOT NULL,
    `answer_id` INT NOT NULL,
    `question_id` INT NOT NULL,
    `technical_score` DECIMAL(4,2) DEFAULT 0.00,
    `matched_concepts` JSON,
    `missing_concepts` JSON,
    `communication_score` DECIMAL(4,2) DEFAULT 0.00,
    `confidence_score` DECIMAL(4,2) DEFAULT 0.00,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `interview_sessions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`answer_id`) REFERENCES `user_answers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`question_id`) REFERENCES `question_bank`(`id`) ON DELETE CASCADE,
    INDEX `idx_eval_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 9: Feedback (Isolated strictly per session)
CREATE TABLE IF NOT EXISTS `interview_feedback` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` INT NOT NULL UNIQUE,
    `overall_score` DECIMAL(4,2) DEFAULT 0.00,
    `technical_score` DECIMAL(4,2) DEFAULT 0.00,
    `communication_score` DECIMAL(4,2) DEFAULT 0.00,
    `confidence_score` DECIMAL(4,2) DEFAULT 0.00,
    `strengths` JSON,
    `weaknesses` JSON,
    `recommendations` JSON,
    `summary_text` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `interview_sessions`(`id`) ON DELETE CASCADE,
    INDEX `idx_feedback_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
