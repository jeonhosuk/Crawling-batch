-- =============================================================================
-- V1__init_schema.sql
-- 최초 스키마 생성 (DB + 테이블)
-- 운영 서버에서 이 파일을 순서대로 실행하면 됨
-- 실행: mysql -u root -p < V1__init_schema.sql
-- =============================================================================

-- 1) 데이터베이스 생성 (없으면 생성, 있으면 무시)
CREATE DATABASE IF NOT EXISTS crawling
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE crawling;

-- 2) HOT_DEALS 테이블 생성
CREATE TABLE IF NOT EXISTS HOT_DEALS (
    id          BIGINT          AUTO_INCREMENT PRIMARY KEY,     -- PK (자동 증가)
    title       VARCHAR(500)    NOT NULL,                       -- 핫딜 제목
    url         VARCHAR(1000)   NOT NULL,                       -- 핫딜 링크
    price       VARCHAR(100)    DEFAULT '',                     -- 가격
    source      VARCHAR(50)     NOT NULL,                       -- 출처 (arca_hotdeal / ppomppu)
    posted_at   VARCHAR(100)    DEFAULT '',                     -- 원글 작성시간
    crawled_at  DATETIME        NOT NULL,                       -- 크롤링 시간
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP,      -- DB 입력 시간 (자동)

    UNIQUE KEY uk_url (url(255))                                -- url 중복 방지 (앞 255자 기준)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
