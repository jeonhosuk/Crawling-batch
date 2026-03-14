# =============================================================================
# base.py - 크롤러 공통 부모 클래스 (추상 클래스)
# - crawl(): 자식 클래스가 구현
# - filter_alcohol(): 주류 키워드 필터링 + 카테고리 분류
# - filter_today(): 오늘 이후 포스팅만 필터링
# - mark_expired(): 크롤링에서 사라진 딜을 EXPIRED로 변경 (앱에서 취소선 표시)
# - save(): DB 저장
# - run(): crawl → filter_today → filter_alcohol → save → mark_expired
#
# ★ 키워드 수정은 config/keywords.py에서 ★
# =============================================================================

import re
from abc import ABC, abstractmethod
from datetime import datetime, date

from loguru import logger

from crawling_batch.config.database import DatabaseManager
from crawling_batch.config.keywords import (
    CATEGORY_KEYWORDS, EXACT_KEYWORDS, GENERAL_ALCOHOL_KEYWORDS, EXCLUDE_KEYWORDS
)
from crawling_batch.model.hotdeal import HotDeal


def _build_patterns():
    """
    일반 키워드(부분 일치) + 정확 키워드(단어 경계 매칭)를 합쳐서 패턴 생성
    정확 키워드: "럼" → (?<![가-힣a-zA-Z])럼(?![가-힣a-zA-Z])
    → "컬럼비아"의 "럼"은 안 걸리고, "럼 할인"의 "럼"은 걸림
    """
    category_patterns = {}
    all_parts = []

    for cat, keywords in CATEGORY_KEYWORDS.items():
        parts = [re.escape(kw) for kw in keywords]
        # 정확 키워드 추가 (단어 경계)
        for exact_kw in EXACT_KEYWORDS.get(cat, []):
            parts.append(f"(?<![가-힣a-zA-Z]){re.escape(exact_kw)}(?![가-힣a-zA-Z])")
        category_patterns[cat] = re.compile("|".join(parts), re.IGNORECASE)
        all_parts.extend(parts)

    # 일반 주류 키워드 추가
    all_parts.extend(re.escape(kw) for kw in GENERAL_ALCOHOL_KEYWORDS)
    alcohol_pattern = re.compile("|".join(all_parts), re.IGNORECASE)

    return category_patterns, alcohol_pattern


CATEGORY_PATTERNS, ALCOHOL_PATTERN = _build_patterns()

# 제외 패턴 (종료/품절/마감 등)
EXCLUDE_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in EXCLUDE_KEYWORDS),
    re.IGNORECASE
)


def classify_category(title: str) -> str:
    """제목에서 주류 카테고리 자동 판별 (WINE, WHISKY, BEER 등)"""
    for category, pattern in CATEGORY_PATTERNS.items():
        if pattern.search(title):
            return category
    return ""


def parse_post_date(posted_at: str) -> date | None:
    """
    다양한 날짜 포맷을 date 객체로 변환
    - 아카: "2026-03-14T00:31:32.000Z" (ISO)
    - 뽐뿌: "26.03.14 13:28:12"
    - 루리웹: "2026.03.14" 또는 "10:12" (시간만 = 오늘)
    """
    if not posted_at:
        return None

    try:
        # ISO 포맷 (아카라이브)
        if "T" in posted_at:
            return datetime.fromisoformat(posted_at.replace("Z", "+00:00")).date()

        # "26.03.14 13:28:12" (뽐뿌)
        if len(posted_at) >= 8 and posted_at[2] == ".":
            return datetime.strptime(posted_at[:8], "%y.%m.%d").date()

        # "2026.03.14" (루리웹)
        if len(posted_at) == 10 and posted_at[4] == ".":
            return datetime.strptime(posted_at, "%Y.%m.%d").date()

        # "10:12" (루리웹 - 시간만 있으면 오늘)
        if ":" in posted_at and len(posted_at) <= 5:
            return date.today()

    except (ValueError, IndexError):
        pass

    return None


class BaseCrawler(ABC):
    """모든 크롤러의 부모 클래스"""

    skip_alcohol_filter = False  # True면 주류 필터 건너뜀 (루리웹처럼 이미 주류 검색인 경우)

    def __init__(self, db: DatabaseManager):
        self.db = db

    @abstractmethod
    async def crawl(self) -> list[HotDeal]:
        """실제 크롤링 로직 - 사이트마다 HTML 구조가 다르므로 각자 구현"""
        pass

    def filter_by_date(self, deals: list[HotDeal]) -> list[HotDeal]:
        """당일 포스팅된 핫딜만 필터링 (날짜 파싱 실패한 건은 포함)"""
        today = date.today()
        filtered = []
        for deal in deals:
            post_date = parse_post_date(deal.posted_at)
            if post_date is None or post_date >= today:
                filtered.append(deal)

        logger.info(
            f"[{self.__class__.__name__}] Date filter: {len(filtered)}/{len(deals)} deals from today"
        )
        return filtered

    def filter_excluded(self, deals: list[HotDeal]) -> list[HotDeal]:
        """제목에 종료/품절/마감 키워드가 있으면 버림"""
        filtered = [d for d in deals if not EXCLUDE_PATTERN.search(d.title)]
        excluded = len(deals) - len(filtered)
        if excluded > 0:
            logger.info(
                f"[{self.__class__.__name__}] Excluded: {excluded} expired/sold-out deals"
            )
        return filtered

    def filter_alcohol(self, deals: list[HotDeal]) -> list[HotDeal]:
        """주류 키워드가 포함된 핫딜만 필터링 + 카테고리 자동 분류"""
        filtered = []
        for deal in deals:
            if ALCOHOL_PATTERN.search(deal.title):
                deal.category = classify_category(deal.title)
                filtered.append(deal)

        logger.info(
            f"[{self.__class__.__name__}] Alcohol filter: {len(filtered)}/{len(deals)} deals"
        )
        return filtered

    def save(self, deals: list[HotDeal]):
        """크롤링 결과를 DB에 저장 (새 딜은 ACTIVE로)"""
        if not deals:
            logger.info(f"[{self.__class__.__name__}] No deals to save")
            return

        query = """
            INSERT INTO HOT_DEALS
                (title, url, price, original_price, delivery_fee,
                 source, shop_name, category, thumbnail, posted_at, crawled_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                price = VALUES(price),
                original_price = VALUES(original_price),
                delivery_fee = VALUES(delivery_fee),
                shop_name = VALUES(shop_name),
                category = VALUES(category),
                thumbnail = VALUES(thumbnail),
                crawled_at = VALUES(crawled_at),
                status = 'ACTIVE'
        """

        for deal in deals:
            try:
                self.db.execute(query, (
                    deal.title,
                    deal.url,
                    deal.price,
                    deal.original_price,
                    deal.delivery_fee,
                    deal.source,
                    deal.shop_name,
                    deal.category,
                    deal.thumbnail,
                    deal.posted_at,
                    deal.crawled_at.strftime("%Y-%m-%d %H:%M:%S"),
                ))
            except Exception as e:
                logger.error(f"[{self.__class__.__name__}] Failed to save deal: {deal.title} - {e}")

        logger.info(f"[{self.__class__.__name__}] Saved {len(deals)} deals")

    def mark_expired(self, current_urls: list[str], source: str):
        """
        이번 크롤링에서 안 보이는 기존 ACTIVE 딜 → EXPIRED로 변경
        앱에서는 EXPIRED인 딜의 제목에 취소선(line-through) 표시
        """
        if not current_urls:
            return

        # %s 플레이스홀더를 URL 개수만큼 생성
        placeholders = ",".join(["%s"] * len(current_urls))
        query = f"""
            UPDATE HOT_DEALS
            SET status = 'EXPIRED'
            WHERE source = %s
              AND status = 'ACTIVE'
              AND url NOT IN ({placeholders})
        """
        params = (source, *current_urls)

        try:
            cursor = self.db.execute(query, params)
            expired_count = cursor.rowcount
            if expired_count > 0:
                logger.info(f"[{self.__class__.__name__}] Marked {expired_count} deals as EXPIRED")
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Failed to mark expired: {e}")

    async def run(self):
        """
        크롤링 전체 흐름:
        1) crawl() - 사이트에서 데이터 수집
        2) filter_today() - 오늘 이후 포스팅만
        3) filter_alcohol() - 주류 키워드 필터 + 카테고리 분류
        4) save() - DB 저장 (ACTIVE 상태)
        5) mark_expired() - 이번에 안 보이는 기존 딜 → EXPIRED (취소선)
        """
        logger.info(f"[{self.__class__.__name__}] Starting crawl...")
        deals = await self.crawl()
        deals = self.filter_by_date(deals)
        deals = self.filter_excluded(deals)
        if not self.skip_alcohol_filter:
            deals = self.filter_alcohol(deals)
        self.save(deals)

        # 이번 크롤링에서 발견된 URL 목록으로 만료 처리
        if deals:
            source = deals[0].source
            current_urls = [d.url for d in deals]
            self.mark_expired(current_urls, source)

        logger.info(f"[{self.__class__.__name__}] Finished. {len(deals)} alcohol deals saved.")
        return deals
