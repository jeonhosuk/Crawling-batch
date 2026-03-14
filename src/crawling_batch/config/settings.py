# =============================================================================
# settings.py - 환경변수 설정 관리
# APP_ENV 값에 따라 .env.dev 또는 .env.prod 파일을 읽음
# Java의 application-dev.yml / application-prod.yml 과 같은 구조
#
# 사용법:
#   개발: APP_ENV=dev  poetry run crawling-batch   (기본값이 dev라서 생략 가능)
#   운영: APP_ENV=prod poetry run crawling-batch
# =============================================================================

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# APP_ENV 환경변수를 먼저 확인 → 없으면 기본값 "dev"
APP_ENV = os.getenv("APP_ENV", "dev")

# APP_ENV에 맞는 .env 파일 로딩 (.env.dev 또는 .env.prod)
load_dotenv(f".env.{APP_ENV}")


class Settings(BaseSettings):
    """
    .env.{APP_ENV} 파일의 값들이 이 클래스의 필드에 자동으로 들어감
    예: .env.dev에 DB_HOST=127.0.0.1 → settings.DB_HOST == "127.0.0.1"
    """
    APP_ENV: str = "dev"                     # 현재 환경 (dev / prod)
    DB_HOST: str = "localhost"               # DB 서버 주소
    DB_PORT: int = 3306                      # DB 포트
    DB_USER: str = "root"                    # DB 접속 계정
    DB_PASSWORD: str = ""                    # DB 비밀번호
    DB_NAME: str = "crawling"                # 사용할 데이터베이스 이름
    CRON_INTERVAL_MINUTES: int = 30          # 크롤링 실행 주기 (분)

    class Config:
        env_file = f".env.{APP_ENV}"         # 환경에 맞는 파일을 읽음


settings = Settings()
