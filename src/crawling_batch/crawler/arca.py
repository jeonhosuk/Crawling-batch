# =============================================================================
# arca.py - 아카라이브 핫딜 게시판 크롤러
# https://arca.live/b/hotdeal 에서 핫딜 목록을 수집
# =============================================================================

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from loguru import logger

from crawling_batch.crawler.base import BaseCrawler
from crawling_batch.model.hotdeal import HotDeal

ARCA_URL = "https://arca.live/b/hotdeal"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class ArcaCrawler(BaseCrawler):
    """아카라이브 핫딜 크롤러"""

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
                await page.goto(ARCA_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)
                content = await page.content()
                await browser.close()

            soup = BeautifulSoup(content, "html.parser")
            articles = soup.select("div.vrow.hybrid")

            for article in articles:
                try:
                    title_el = article.select_one("a.title.hybrid-title")
                    if not title_el:
                        continue

                    # 댓글 수 제거
                    for info in title_el.select(".info"):
                        info.decompose()
                    title = title_el.get_text(strip=True)

                    # 링크
                    href = title_el.get("href", "")
                    url = f"https://arca.live{href}" if href.startswith("/") else href

                    # 작성 시간: ISO → "2026.03.14 09:31" 형태로 변환
                    time_el = article.select_one(".vcol.col-time time")
                    posted_at = ""
                    if time_el:
                        raw = time_el.get("datetime", "")
                        if raw:
                            from datetime import datetime as dt
                            try:
                                parsed = dt.fromisoformat(raw.replace("Z", "+00:00"))
                                posted_at = parsed.strftime("%Y.%m.%d %H:%M")
                            except ValueError:
                                posted_at = raw

                    # 가격: <span class="deal-price">10,730원</span>
                    price_el = article.select_one(".deal-price")
                    price = price_el.get_text(strip=True) if price_el else ""

                    # 쇼핑몰명: <span class="deal-store">쿠팡</span>
                    shop_el = article.select_one(".deal-store")
                    shop_name = shop_el.get_text(strip=True) if shop_el else ""

                    # 배송비: <span class="deal-delivery">무료</span>
                    delivery_el = article.select_one(".deal-delivery")
                    delivery_fee = delivery_el.get_text(strip=True) if delivery_el else ""

                    deals.append(HotDeal(
                        title=title,
                        url=url,
                        price=price,
                        delivery_fee=delivery_fee,
                        source="arca_hotdeal",
                        shop_name=shop_name,
                        posted_at=posted_at,
                    ))
                except Exception as e:
                    logger.warning(f"[ArcaCrawler] Failed to parse article: {e}")

        except Exception as e:
            logger.error(f"[ArcaCrawler] Crawl failed: {e}")

        return deals
