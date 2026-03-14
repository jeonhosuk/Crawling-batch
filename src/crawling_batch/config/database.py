# =============================================================================
# database.py - MariaDB 연결 및 쿼리 실행 담당
# Spring의 JdbcTemplate과 비슷한 역할
# 연결(connect), 쿼리 실행(execute), 조회(fetch_all), 종료(disconnect)
# =============================================================================

import pymysql                               # MariaDB/MySQL 연결 드라이버
from loguru import logger                    # 로그 출력 라이브러리

from crawling_batch.config.settings import settings  # .env에서 읽어온 DB 접속 정보


class DatabaseManager:
    """DB 연결/쿼리를 한 곳에서 관리하는 클래스"""

    def __init__(self):
        self.connection = None               # DB 연결 객체 (처음엔 연결 안 된 상태)

    def connect(self):
        """MariaDB에 연결"""
        self.connection = pymysql.connect(
            host=settings.DB_HOST,           # settings.py에서 가져온 접속 정보
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset="utf8mb4",               # 한글 + 이모지 지원 인코딩
            cursorclass=pymysql.cursors.DictCursor,  # 조회 결과를 딕셔너리로 반환 ({"컬럼명": "값"})
        )
        logger.info("Database connected")

    def disconnect(self):
        """DB 연결 종료"""
        if self.connection:
            self.connection.close()
            logger.info("Database disconnected")

    def execute(self, query: str, params: tuple = None):
        """
        INSERT, UPDATE, DELETE 등 데이터를 변경하는 쿼리 실행
        - 연결이 끊겼으면 자동으로 재연결
        - 실패하면 rollback(되돌리기) 후 에러를 다시 던짐
        - params의 값이 %s 자리에 순서대로 들어감 (SQL Injection 방지)
        """
        try:
            if not self.connection or not self.connection.open:
                self.connect()               # 연결 끊겼으면 자동 재연결
            with self.connection.cursor() as cursor:
                cursor.execute(query, params) # 쿼리 실행
                self.connection.commit()      # DB에 확정 반영
                return cursor
        except Exception as e:
            logger.error(f"Database error: {e}")
            if self.connection:
                self.connection.rollback()    # 에러 시 변경사항 취소
            raise                             # 에러를 상위 호출자에게 다시 던짐

    def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """
        SELECT 쿼리 실행 → 결과를 딕셔너리 리스트로 반환
        예: [{"title": "핫딜1", "price": "10000"}, {"title": "핫딜2", ...}]
        """
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()     # 모든 행을 가져옴
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
