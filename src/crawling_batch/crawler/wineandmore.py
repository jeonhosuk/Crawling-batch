# =============================================================================
# wineandmore.py - 와인앤모어(신세계L&B) 프로모션 크롤러
# https://www.shinsegae-lnb.com/html/news/promotion.html 에서 행사 정보 수집
# 월 1회 프로모션 업데이트 → 주류 전문이라 키워드 필터 불필요
# =============================================================================

import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from loguru import logger

from crawling_batch.crawler.base import BaseCrawler
from crawling_batch.model.hotdeal import HotDeal

WINEANDMORE_URL = "https://www.shinsegae-lnb.com/html/news/promotion.html"
WINEANDMORE_BASE = "https://www.shinsegae-lnb.com"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# alt 텍스트에서 날짜 추출: (2026/03/05 ~ 2026/03/31)
DATE_PATTERN = re.compile(r"\((\d{4}/\d{2}/\d{2})\s*~\s*(\d{4}/\d{2}/\d{2})\)")


class WineAndMoreCrawler(BaseCrawler):
    """와인앤모어 프로모션 크롤러 - 주류 전문이라 필터 스킵"""

    skip_alcohol_filter = True  # 와인앤모어는 전부 주류 행사

    async def crawl(self) -> list[HotDeal]:
        deals = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(user_agent=USER_AGENT)
                page = await context.new_page()
                await page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', { get: () => false });"
                )
                await page.goto(WINEANDMORE_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)
                content = await page.content()
                await browser.close()

            soup = BeautifulSoup(content, "html.parser")
            # 각 프로모션: <div class="list"> 안에 <a>, <img>
            items = soup.select(".promotionGallery .list")

            for item in items:
                try:
                    link_el = item.select_one("a")
                    if not link_el:
                        continue

                    # 이미지 (PC 버전)
                    img_el = item.select_one("img.pcView")
                    if not img_el:
                        continue

                    # alt 텍스트에서 제목 + 날짜 추출
                    # "2026년 3월 왬 행사 안내 (2026/03/05 ~ 2026/03/31)"
                    alt = img_el.get("alt", "")
                    title = alt.split("(")[0].strip() if "(" in alt else alt

                    # 날짜 (행사 기간)
                    date_match = DATE_PATTERN.search(alt)
                    posted_at = ""
                    if date_match:
                        posted_at = f"{date_match.group(1)} ~ {date_match.group(2)}"

                    # 썸네일 이미지 URL
                    img_src = img_el.get("src", "")
                    thumbnail = f"{WINEANDMORE_BASE}{img_src}" if img_src.startswith("/") else img_src

                    # 링크: onclick="viewData('884')" → 상세 페이지 URL 생성
                    onclick = link_el.get("onclick", "")
                    promo_id = ""
                    id_match = re.search(r"viewData\('(\d+)'\)", onclick)
                    if id_match:
                        promo_id = id_match.group(1)
                    # 상세 페이지 URL: promotionView.html?idx=884
                    url = f"{WINEANDMORE_BASE}/html/news/promotionView.html?idx={promo_id}" if promo_id else WINEANDMORE_URL

                    deals.append(HotDeal(
                        title=title,
                        url=url,
                        source="wineandmore",
                        shop_name="와인앤모어",
                        category="WINE",  # 와인앤모어는 기본 WINE 카테고리
                        thumbnail=thumbnail,
                        posted_at=posted_at,
                    ))
                except Exception as e:
                    logger.warning(f"[WineAndMoreCrawler] Failed to parse item: {e}")

        except Exception as e:
            logger.error(f"[WineAndMoreCrawler] Crawl failed: {e}")

        return deals

    async def run(self):
        """와인앤모어 전용 run() - 월 1회 프로모션이라 날짜/주류 필터 스킵, 최신 1건만 저장"""
        logger.info(f"[WineAndMoreCrawler] Starting crawl...")
        deals = await self.crawl()

        # 최신 프로모션 1건만 저장 (맨 위가 최신)
        if deals:
            deals = [deals[0]]

        self.save(deals)
        logger.info(f"[WineAndMoreCrawler] Finished. {len(deals)} promotion saved.")
        return deals
