# =============================================================================
# hotdeal.py - 핫딜 데이터 모델
# 크롤링한 핫딜 1건의 데이터 구조를 정의
# Java의 DTO/Entity 클래스, TypeScript의 interface와 같은 역할
# =============================================================================

from datetime import datetime
from pydantic import BaseModel, Field


class HotDeal(BaseModel):
    """
    핫딜 1건의 데이터를 담는 모델
    DB의 HOT_DEALS 테이블 한 행(row)과 대응됨
    """
    title: str                               # 핫딜 제목 (필수값)
    url: str                                 # 핫딜 링크 (필수값)
    price: str = ""                          # 할인가 (예: "19,900원")
    original_price: str = ""                 # 원가 (예: "29,800원", 할인율 계산용)
    delivery_fee: str = ""                   # 배송비 (예: "무료", "3,000원")
    source: str                              # 출처 (필수) - "arca_hotdeal" 또는 "ppomppu"
    shop_name: str = ""                      # 쇼핑몰명 (예: "쿠팡", "네이버", "11번가")
    category: str = ""                       # 카테고리 (예: "whisky", "beer", "wine")
    thumbnail: str = ""                      # 썸네일 이미지 URL
    posted_at: str = ""                      # 원글 작성 시간
    crawled_at: datetime = Field(            # 크롤링한 시간 (자동으로 현재 시간 입력됨)
        default_factory=datetime.now
    )
    status: str = "ACTIVE"                   # 상태: ACTIVE(진행중) / EXPIRED(종료→취소선)
