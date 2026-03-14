# =============================================================================
# main.py - 프로그램 시작점 (엔트리포인트)
#
# 스케줄 구조:
#   - 핫딜 크롤러 (아카/뽐뿌/루리웹): 30분마다
#   - 와인앤모어 프로모션: 하루 1회 (매일 오전 9시)
# =============================================================================

import asyncio
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from crawling_batch.config import settings, DatabaseManager
from crawling_batch.crawler import ArcaCrawler, PpomppuCrawler, RuliwebCrawler, WineAndMoreCrawler

# =============================================================================
# 로깅 설정
# =============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}"
)
logger.add(
    "logs/crawling_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)


def run_hotdeal_crawlers():
    """핫딜 크롤러 실행 (30분마다) - 아카라이브, 뽐뿌, 루리웹"""
    logger.info("=== Hotdeal crawling job started ===")
    db = DatabaseManager()

    try:
        db.connect()
        crawlers = [
            ArcaCrawler(db),
            PpomppuCrawler(db),
            RuliwebCrawler(db),
        ]

        async def crawl_all():
            for crawler in crawlers:
                try:
                    await crawler.run()
                except Exception as e:
                    logger.error(f"Crawler failed: {crawler.__class__.__name__} - {e}")

        asyncio.run(crawl_all())
    finally:
        db.disconnect()

    logger.info("=== Hotdeal crawling job finished ===")


def run_promotion_crawlers():
    """프로모션 크롤러 실행 (하루 1회) - 와인앤모어"""
    logger.info("=== Promotion crawling job started ===")
    db = DatabaseManager()

    try:
        db.connect()
        crawlers = [
            WineAndMoreCrawler(db),
        ]

        async def crawl_all():
            for crawler in crawlers:
                try:
                    await crawler.run()
                except Exception as e:
                    logger.error(f"Crawler failed: {crawler.__class__.__name__} - {e}")

        asyncio.run(crawl_all())
    finally:
        db.disconnect()

    logger.info("=== Promotion crawling job finished ===")


def main():
    """프로그램 메인 함수"""
    logger.info("Crawling batch service starting...")

    # 시작 시 전체 1회 실행
    run_hotdeal_crawlers()
    run_promotion_crawlers()

    # 스케줄러 등록
    scheduler = BlockingScheduler()

    # 핫딜: 30분마다
    scheduler.add_job(
        run_hotdeal_crawlers,
        "interval",
        minutes=settings.CRON_INTERVAL_MINUTES,
        id="hotdeal_job",
    )
    logger.info(f"Hotdeal schedule: every {settings.CRON_INTERVAL_MINUTES} minutes")

    # 프로모션: 매일 오전 9시
    scheduler.add_job(
        run_promotion_crawlers,
        "cron",
        hour=9,
        minute=0,
        id="promotion_job",
    )
    logger.info("Promotion schedule: daily at 09:00")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Crawling batch service stopped.")


if __name__ == "__main__":
    main()
