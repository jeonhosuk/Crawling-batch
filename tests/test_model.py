from crawling_batch.model.hotdeal import HotDeal


def test_hotdeal_creation():
    deal = HotDeal(
        title="Test Deal",
        url="https://example.com/deal/1",
        price="10,000원",
        source="arca_hotdeal",
        posted_at="2026-01-01 12:00:00",
    )
    assert deal.title == "Test Deal"
    assert deal.source == "arca_hotdeal"
    assert deal.price == "10,000원"


def test_hotdeal_defaults():
    deal = HotDeal(
        title="Minimal Deal",
        url="https://example.com/deal/2",
        source="ppomppu",
    )
    assert deal.price == ""
    assert deal.posted_at == ""
    assert deal.crawled_at is not None
