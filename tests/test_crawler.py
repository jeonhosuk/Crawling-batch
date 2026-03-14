from crawling_batch.crawler.base import BaseCrawler
from crawling_batch.model.hotdeal import HotDeal


class FakeCrawler(BaseCrawler):
    async def crawl(self) -> list[HotDeal]:
        return [
            HotDeal(title="Fake Deal", url="https://example.com/1", source="test"),
        ]


def test_fake_crawler_instantiation():
    crawler = FakeCrawler(db=None)
    assert crawler.db is None


async def test_fake_crawler_crawl():
    crawler = FakeCrawler(db=None)
    deals = await crawler.crawl()
    assert len(deals) == 1
    assert deals[0].source == "test"
