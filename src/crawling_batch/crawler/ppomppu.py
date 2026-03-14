# =============================================================================
# ppomppu.py - 뽐뿌 핫딜 게시판 크롤러
# https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu 에서 핫딜 목록 수집
# 뽐뿌는 제목에 "[쇼핑몰] 상품명 (가격/배송비)" 형식으로 정보가 들어있음
# =============================================================================

import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from loguru import logger

from crawling_batch.crawler.base import BaseCrawler
from crawling_batch.model.hotdeal import HotDeal

PPOMPPU_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# 제목에서 가격/배송비 추출 정규식
# 예: "(19,900원/무료)" → price="19,900원", delivery="무료"
PRICE_PATTERN = re.compile(r"\(([0-9,]+원)\s*/\s*(.+?)\)")


class PpomppuCrawler(BaseCrawler):
    """뽐뿌 핫딜 크롤러"""

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
                await page.goto(PPOMPPU_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)
                content = await page.content()
                await browser.close()

            soup = BeautifulSoup(content, "html.parser")
            rows = soup.select("tr.baseList.bbs_new1")

            for row in rows:
                try:
                    title_el = row.select_one("a.baseList-title")
                    if not title_el:
                        continue

                    # 제목 전체 텍스트
                    title_span = title_el.select_one("span")
                    full_title = title_span.get_text(strip=True) if title_span else title_el.get_text(strip=True)

                    # 쇼핑몰명: <em class="subject_preface">[쿠팡]</em>
                    shop_el = title_el.select_one("em.subject_preface")
                    shop_name = shop_el.get_text(strip=True).strip("[]") if shop_el else ""

                    # 제목에서 가격/배송비 파싱: "(19,900원/무료)"
                    price = ""
                    delivery_fee = ""
                    price_match = PRICE_PATTERN.search(full_title)
                    if price_match:
                        price = price_match.group(1)          # "19,900원"
                        delivery_fee = price_match.group(2)   # "무료" 또는 "3,000원"

                    # 링크
                    href = title_el.get("href", "")
                    url = f"https://www.ppomppu.co.kr/zboard/{href}" if not href.startswith("http") else href

                    # 작성 시간: <td title="26.03.14 13:28:12">
                    time_td = row.select_one("td[title]")
                    posted_at = time_td.get("title", "") if time_td else ""

                    # 썸네일: <a class="baseList-thumb"><img src="...">
                    thumb_el = row.select_one("a.baseList-thumb img")
                    thumbnail = ""
                    if thumb_el:
                        thumb_src = thumb_el.get("src", "")
                        # 뽐뿌 썸네일은 //로 시작하는 상대 프로토콜 URL
                        thumbnail = f"https:{thumb_src}" if thumb_src.startswith("//") else thumb_src

                    deals.append(HotDeal(
                        title=full_title,
                        url=url,
                        price=price,
                        delivery_fee=delivery_fee,
                        source="ppomppu",
                        shop_name=shop_name,
                        thumbnail=thumbnail,
                        posted_at=posted_at,
                    ))
                except Exception as e:
                    logger.warning(f"[PpomppuCrawler] Failed to parse row: {e}")

        except Exception as e:
            logger.error(f"[PpomppuCrawler] Crawl failed: {e}")

        return deals
