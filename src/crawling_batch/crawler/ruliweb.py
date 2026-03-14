# =============================================================================
# ruliweb.py - 루리웹 핫딜 게시판 크롤러
# https://bbs.ruliweb.com/news/board/1020 에서 주류 키워드로 검색된 핫딜 수집
# 키워드별로 최대 3페이지까지 목록 크롤링
# + 각 글 상세 페이지에 들어가서 실제 쇼핑몰 링크 추출
# =============================================================================

from datetime import date
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from loguru import logger

from crawling_batch.crawler.base import BaseCrawler
from crawling_batch.model.hotdeal import HotDeal

RULIWEB_BASE = "https://bbs.ruliweb.com/news/board/1020"
# { 검색 키워드: 카테고리 코드 }
SEARCH_KEYWORDS = {
    "위스키": "WHISKY",
    "와인": "WINE",
    "맥주": "BEER",
    "소주": "KOREAN_TRADITIONAL",
    "사케": "SAKE",
    "양주": "WHISKY",
    "주류": "",
}
MAX_PAGES = 3

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# 루리웹 내부 도메인 (이건 실제 쇼핑몰 링크가 아니므로 건너뜀)
# 루리웹 내부 링크는 실제 쇼핑몰 링크가 아니므로 건너뜀
SKIP_DOMAINS = {"ruliweb.com", "m.ruliweb.com", "bbs.ruliweb.com"}


class RuliwebCrawler(BaseCrawler):
    """루리웹 핫딜 크롤러 - 상세 페이지에서 실제 쇼핑몰 링크 추출"""

    skip_alcohol_filter = False  # 루리웹 검색 결과에 주류 아닌 글도 섞여 나오므로 필터 필요

    def _parse_rows(self, soup, seen_urls) -> list[HotDeal]:
        """목록 페이지에서 게시글 파싱 (제목, 루리웹 URL, 시간 등)"""
        deals = []
        rows = soup.select("tr.table_body.blocktarget")

        for row in rows:
            try:
                if "notice" in row.get("class", []):
                    continue

                title_el = row.select_one("a.subject_link.deco")
                if not title_el:
                    continue

                href = title_el.get("href", "")
                # URL에서 검색 파라미터 제거 → 중복 방지
                # "...read/100275?search_type=subject&search_key=위스키" → "...read/100275"
                clean_url = href.split("?")[0] if "?" in href else href
                if clean_url in seen_urls:
                    continue
                seen_urls.add(clean_url)
                href = clean_url

                for tag in title_el.select(".num_reply, i"):
                    tag.decompose()
                title = title_el.get_text(strip=True)

                shop_tag = title_el.select_one(".subject_tag")
                shop_name = shop_tag.get_text(strip=True).strip("[]") if shop_tag else ""

                time_el = row.select_one("td.time")
                posted_at = time_el.get_text(strip=True) if time_el else ""
                if posted_at and ":" in posted_at and "." not in posted_at:
                    posted_at = f"{date.today().strftime('%Y.%m.%d')} {posted_at}"

                deals.append(HotDeal(
                    title=title,
                    url=href,              # 일단 루리웹 URL (나중에 실제 링크로 교체)
                    source="ruliweb",
                    shop_name=shop_name,
                    posted_at=posted_at,
                ))
            except Exception as e:
                logger.warning(f"[RuliwebCrawler] Failed to parse row: {e}")

        return deals

    async def _extract_real_url(self, context, ruliweb_url: str) -> str:
        """
        상세 페이지에 들어가서 본문의 첫 번째 외부 링크(실제 쇼핑몰 URL) 추출
        못 찾으면 루리웹 URL 그대로 반환
        """
        try:
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => false });"
            )
            await page.goto(ruliweb_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            content = await page.content()
            await page.close()

            soup = BeautifulSoup(content, "html.parser")
            # 본문 영역: <div class="view_content autolink">
            body = soup.select_one("div.view_content")
            if not body:
                return ruliweb_url

            # 본문 내 모든 <a> 태그에서 외부 링크 찾기
            for link in body.select("a[href]"):
                href = link.get("href", "")
                if not href or not href.startswith("http"):
                    continue
                # 루리웹 내부 링크는 건너뜀
                domain = urlparse(href).netloc.lower()
                if any(skip in domain for skip in SKIP_DOMAINS):
                    continue
                return href  # 첫 번째 외부 링크 = 실제 쇼핑몰 링크

        except Exception as e:
            logger.warning(f"[RuliwebCrawler] Failed to get real URL from {ruliweb_url}: {e}")

        return ruliweb_url  # 실패 시 루리웹 URL 유지

    async def crawl(self) -> list[HotDeal]:
        deals = []
        seen_urls = set()

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(user_agent=USER_AGENT)

                # ── Step 1: 목록 페이지에서 게시글 수집 ──
                for keyword, category in SEARCH_KEYWORDS.items():
                    for page_num in range(1, MAX_PAGES + 1):
                        try:
                            page = await context.new_page()
                            await page.add_init_script(
                                "Object.defineProperty(navigator, 'webdriver', { get: () => false });"
                            )

                            url = f"{RULIWEB_BASE}?search_type=subject&search_key={keyword}&page={page_num}"
                            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                            await page.wait_for_timeout(2000)
                            content = await page.content()
                            await page.close()

                            soup = BeautifulSoup(content, "html.parser")
                            page_deals = self._parse_rows(soup, seen_urls)

                            for deal in page_deals:
                                if category:
                                    deal.category = category

                            deals.extend(page_deals)

                            logger.info(
                                f"[RuliwebCrawler] '{keyword}' page {page_num}: {len(page_deals)} posts"
                            )

                            if not page_deals:
                                break

                        except Exception as e:
                            logger.error(f"[RuliwebCrawler] Failed '{keyword}' page {page_num}: {e}")
                            break

                await browser.close()

        except Exception as e:
            logger.error(f"[RuliwebCrawler] Crawl failed: {e}")

        return deals

    async def run(self):
        """
        루리웹 전용 run() - 날짜/종료 필터 후 상세 페이지 크롤링
        (전체 163건이 아니라 필터 후 남은 건만 상세 접속 → 시간 절약)
        """
        logger.info(f"[RuliwebCrawler] Starting crawl...")
        deals = await self.crawl()
        deals = self.filter_by_date(deals)
        deals = self.filter_excluded(deals)
        deals = self.filter_alcohol(deals)

        # 필터 후 남은 건만 상세 페이지에서 실제 링크 추출 (새 브라우저로)
        if deals:
            logger.info(f"[RuliwebCrawler] Extracting real URLs from {len(deals)} filtered posts...")
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(user_agent=USER_AGENT)
                for deal in deals:
                    real_url = await self._extract_real_url(context, deal.url)
                    if real_url != deal.url:
                        deal.url = real_url
                await browser.close()

        self.save(deals)

        if deals:
            source = deals[0].source
            current_urls = [d.url for d in deals]
            self.mark_expired(current_urls, source)

        logger.info(f"[RuliwebCrawler] Finished. {len(deals)} deals saved.")
        return deals
