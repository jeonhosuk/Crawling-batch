-- =============================================================================
-- V3__add_status_column.sql
-- 핫딜 상태 관리 컬럼 추가
-- ACTIVE: 진행중 / EXPIRED: 행사 종료 (앱에서 취소선으로 표시)
-- 실행: mysql -u root -p crawling < V3__add_status_column.sql
-- =============================================================================

USE crawling;

ALTER TABLE HOT_DEALS ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE' AFTER crawled_at;

-- status로 조회할 일이 많으므로 인덱스 추가
ALTER TABLE HOT_DEALS ADD INDEX idx_status (status);

-- source + status 복합 인덱스 (크롤러별 만료 처리용)
ALTER TABLE HOT_DEALS ADD INDEX idx_source_status (source, status);
