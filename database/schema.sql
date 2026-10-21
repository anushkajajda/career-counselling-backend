-- =========================================================
-- AI-Based Career Counselling & Skill Gap Analysis Platform
-- Database Schema
-- =========================================================

CREATE DATABASE IF NOT EXISTS career_counselling;

USE career_counselling;


-- =========================================================
-- 1. USERS
-- Stores login/signup information
-- =========================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 2. STUDENT PROFILES
-- Stores student's educational and personal career information
-- =========================================================

CREATE TABLE IF NOT EXISTS student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    education_level VARCHAR(100),
    course VARCHAR(150),
    specialization VARCHAR(150),
    institution VARCHAR(200),
    graduation_year YEAR,
    career_goal VARCHAR(200),
    interests TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_profile_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- =========================================================
-- 3. ASSESSMENTS
-- Stores each career assessment attempt
-- =========================================================

CREATE TABLE IF NOT EXISTS assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'completed',

    CONSTRAINT fk_assessment_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- =========================================================
-- 4. ASSESSMENT ANSWERS
-- Stores answers given by the student
-- =========================================================

CREATE TABLE IF NOT EXISTS assessment_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    question_id INT NOT NULL,
    answer VARCHAR(255) NOT NULL,

    CONSTRAINT fk_answer_assessment
        FOREIGN KEY (assessment_id)
        REFERENCES assessments(id)
        ON DELETE CASCADE
);


-- =========================================================
-- 5. CAREER PATHS
-- Stores available career options
-- =========================================================

CREATE TABLE IF NOT EXISTS career_paths (
    id INT AUTO_INCREMENT PRIMARY KEY,
    career_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 6. SKILLS
-- Stores technical and professional skills
-- =========================================================

CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100),
    description TEXT
);


-- =========================================================
-- 7. CAREER SKILLS
-- Maps careers to their required skills
-- =========================================================

CREATE TABLE IF NOT EXISTS career_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    career_id INT NOT NULL,
    skill_id INT NOT NULL,
    importance DECIMAL(5,2) DEFAULT 1.00,

    CONSTRAINT fk_career_skill_career
        FOREIGN KEY (career_id)
        REFERENCES career_paths(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_career_skill_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(id)
        ON DELETE CASCADE,

    UNIQUE (career_id, skill_id)
);


-- =========================================================
-- 8. USER SKILLS
-- Stores skills currently possessed by a student
-- =========================================================

CREATE TABLE IF NOT EXISTS user_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency_level VARCHAR(50) DEFAULT 'Beginner',

    CONSTRAINT fk_user_skill_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_skill_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(id)
        ON DELETE CASCADE,

    UNIQUE (user_id, skill_id)
);


-- =========================================================
-- 9. CAREER RECOMMENDATIONS
-- Stores career recommendations generated for students
-- =========================================================

CREATE TABLE IF NOT EXISTS career_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_id INT,
    career_id INT NOT NULL,
    recommendation_score DECIMAL(6,2),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_recommendation_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_recommendation_assessment
        FOREIGN KEY (assessment_id)
        REFERENCES assessments(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_recommendation_career
        FOREIGN KEY (career_id)
        REFERENCES career_paths(id)
        ON DELETE CASCADE
);


-- =========================================================
-- 10. SKILL GAPS
-- Stores missing skills for a recommended career
-- =========================================================

CREATE TABLE IF NOT EXISTS skill_gaps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    career_id INT NOT NULL,
    skill_id INT NOT NULL,
    current_level VARCHAR(50),
    required_level VARCHAR(50),
    gap_status VARCHAR(50) DEFAULT 'Needs Improvement',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_skill_gap_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_skill_gap_career
        FOREIGN KEY (career_id)
        REFERENCES career_paths(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_skill_gap_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(id)
        ON DELETE CASCADE
);


-- =========================================================
-- 11. LEARNING ROADMAPS
-- Stores AI-generated learning roadmap
-- =========================================================

CREATE TABLE IF NOT EXISTS learning_roadmaps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    career_id INT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_roadmap_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_roadmap_career
        FOREIGN KEY (career_id)
        REFERENCES career_paths(id)
        ON DELETE SET NULL
);


-- =========================================================
-- 12. ROADMAP ITEMS
-- Individual learning steps inside a roadmap
-- =========================================================

CREATE TABLE IF NOT EXISTS roadmap_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roadmap_id INT NOT NULL,
    skill_id INT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    resource_type VARCHAR(100),
    resource_url VARCHAR(500),
    sequence_order INT DEFAULT 1,
    status VARCHAR(50) DEFAULT 'Not Started',

    CONSTRAINT fk_roadmap_item_roadmap
        FOREIGN KEY (roadmap_id)
        REFERENCES learning_roadmaps(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_roadmap_item_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(id)
        ON DELETE SET NULL
);


-- =========================================================
-- DATABASE SETUP COMPLETE
-- =========================================================