-- =============================================================================
-- V2__add_deal_detail_columns.sql
-- 핫딜 카드 UI에 필요한 컬럼 추가 (카테고리, 썸네일, 원가, 배송비)
-- 실행: mysql -u root -p crawling < V2__add_deal_detail_columns.sql
-- =============================================================================

USE crawling;

-- 카테고리 (주류 필터링용: whisky, beer, wine, soju, sake, etc)
ALTER TABLE HOT_DEALS ADD COLUMN category VARCHAR(50) DEFAULT '' AFTER source;

-- 썸네일 이미지 URL
ALTER TABLE HOT_DEALS ADD COLUMN thumbnail VARCHAR(1000) DEFAULT '' AFTER category;

-- 원가 (할인 전 가격, 할인율 계산용)
ALTER TABLE HOT_DEALS ADD COLUMN original_price VARCHAR(100) DEFAULT '' AFTER price;

-- 배송비
ALTER TABLE HOT_DEALS ADD COLUMN delivery_fee VARCHAR(50) DEFAULT '' AFTER original_price;

-- 쇼핑몰명 (쿠팡, 네이버, 11번가 등)
ALTER TABLE HOT_DEALS ADD COLUMN shop_name VARCHAR(100) DEFAULT '' AFTER source;
