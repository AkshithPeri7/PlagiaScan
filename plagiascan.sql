-- ============================================================
-- PlagiaScan Database  |  Team: Innovators Hub  |  H4T-019
-- Run: mysql -u root -p < plagascan.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS plagiascan;
USE plagiascan;

-- ── TABLE 1: Users ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    u_id         INT AUTO_INCREMENT PRIMARY KEY,
    email        VARCHAR(255) NOT NULL UNIQUE,
    name         VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20)  NOT NULL,
    password     VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── TABLE 2: Plagiarism History ──────────────────────────────
CREATE TABLE IF NOT EXISTS plagiarism_history (
    history_id            INT AUTO_INCREMENT PRIMARY KEY,
    u_id                  INT NOT NULL,
    project_name          VARCHAR(255) NOT NULL,
    date                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score                 FLOAT NOT NULL DEFAULT 0.0,
    status                VARCHAR(50) NOT NULL DEFAULT 'Clean',
    plagiarized_percentage FLOAT DEFAULT 0.0,
    file_content          TEXT,
    result_details        TEXT,
    FOREIGN KEY (u_id) REFERENCES users(u_id) ON DELETE CASCADE
);

-- ── TABLE 3: Backend Developers ─────────────────────────────
-- Passwords stored as plain text for hackathon (easy to verify)
-- In production: replace with bcrypt hashes
CREATE TABLE IF NOT EXISTS backend_developers (
    bd_id       VARCHAR(10)  NOT NULL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    dob         DATE         NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Seed: 5 Real Backend Developers ────────────────────────
-- Passwords stored plain-text (Flask does plain-text fallback for dev accounts)
INSERT INTO backend_developers (bd_id, name, dob, email, password, designation) VALUES
('PS001', 'Akshith',   '2006-11-01', 'akshith@ps',   'akshith001',   'Cr.Dev'),
('PS002', 'Joel',      '2007-03-28', 'joel@ps',       'joel002',       'Cr.Dev'),
('PS003', 'Mufaddal',  '2004-08-31', 'mufaddal@ps',  'mufaddal003',  'Admin'),
('PS004', 'George',    '2006-09-04', 'george@ps',     'george004',     'Jr.Dev'),
('PS005', 'David',     '2005-10-10', 'david@ps',      'david005',      'Jr.Dev');

-- ── Web Traffic Log ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS web_traffic (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active_users INT DEFAULT 0,
    page_visited VARCHAR(255)
);

-- ── Error Logs ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS error_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    issue_type  VARCHAR(100),
    description TEXT,
    status      VARCHAR(50) DEFAULT 'Open'
);

-- ── Accessed Websites (by AI) ────────────────────────────────
CREATE TABLE IF NOT EXISTS accessed_websites (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    website_url     VARCHAR(500),
    check_id        INT,
    relevance_score FLOAT DEFAULT 0.0
);

-- ── Sample Traffic Data ──────────────────────────────────────
INSERT INTO web_traffic (timestamp, active_users, page_visited) VALUES
(NOW() - INTERVAL 11 HOUR,  3,  '/main'),
(NOW() - INTERVAL 10 HOUR,  8,  '/main'),
(NOW() - INTERVAL 9  HOUR, 15,  '/check'),
(NOW() - INTERVAL 8  HOUR, 22,  '/check'),
(NOW() - INTERVAL 7  HOUR, 18,  '/main'),
(NOW() - INTERVAL 6  HOUR, 35,  '/check'),
(NOW() - INTERVAL 5  HOUR, 48,  '/check'),
(NOW() - INTERVAL 4  HOUR, 41,  '/history'),
(NOW() - INTERVAL 3  HOUR, 55,  '/check'),
(NOW() - INTERVAL 2  HOUR, 38,  '/main'),
(NOW() - INTERVAL 1  HOUR, 27,  '/profile'),
(NOW(),                     14,  '/main');

-- ── Sample Error Logs ────────────────────────────────────────
INSERT INTO error_logs (issue_type, description, status) VALUES
('API Timeout',   'Google CSE took >10s for large code file',   'Resolved'),
('DB Connection', 'MySQL pool exhausted during peak usage',      'Resolved'),
('Upload Error',  'File size > 5MB rejected by input handler',   'Open');

SELECT 'PlagiaScan DB setup complete!' AS message;
SELECT 'Developer logins ready:' AS info;
SELECT bd_id, name, email, password, designation FROM backend_developers;
