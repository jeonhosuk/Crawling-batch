# 🍾 Crawling-batch

Casky 앱 연동 주류 핫딜 크롤링 배치 서버

Casky 서비스에 제공되는 주류 핫딜 정보를 자동으로 수집하는 크롤링 Batch 서버입니다.  
지정된 스케줄에 따라 각 커뮤니티와 주류 전문 사이트의 게시글을 크롤링하고  
필터링하여 데이터베이스에 저장합니다.

---

## 🛠 환경 요구사항 (Prerequisites)

| 항목 | 버전 | 비고 |
|---|---|---|
| Language | Python 3.14+ | |
| Package Manager | Poetry 2.3.2+ | 의존성 관리 |
| Database | MariaDB 10.11+ | Data 스토리지 분리 환경 권장 |
| OS | Ubuntu 22.04+ / Windows 11 | |

---

## 📦 주요 설치 패키지 (Tech Stack)

| 패키지 | 버전 | 용도 |
|---|---|---|
| playwright | 1.58.0 | 브라우저 크롤링 |
| playwright-stealth | 2.0.2 | 봇 감지 우회 |
| beautifulsoup4 | 4.14.3 | HTML 파싱 |
| requests | 2.32.5 | HTTP 요청 |
| pymysql | 1.1.2 | MariaDB 연결 |
| python-dotenv | 1.2.2 | 환경변수 로딩 |
| apscheduler | 3.11.2 | 스케줄 실행 |
| loguru | 0.7.3 | 로깅 |
| pydantic / pydantic-settings | 2.x | 데이터 검증 |

---

## 📁 프로젝트 구조


src/crawling_batch/

├── config/

│ ├── settings.py

│ ├── database.py

│ └── keywords.py

├── crawler/

│ ├── base.py

│ ├── arca.py

│ ├── ppomppu.py

│ ├── ruliweb.py

│ └── wineandmore.py

├── model/

│ └── hotdeal.py

└── main.py


---

## 🕸 크롤링 대상 및 스케줄

| 사이트 | 실행 주기 | 조건 |
|---|---|---|
| 아카라이브 핫딜 | 2시간 | 당일 게시물 + 주류 키워드 |
| 뽐뿌 핫딜 | 2시간 | 당일 게시물 + 주류 키워드 |
| 루리웹 핫딜 | 2시간 | 키워드 + 상세 링크 |
| 와인앤모어 | 하루 1회 (09:00) | 주류 프로모션 |

---

## 🚀 Deployment

### 1️⃣ 시스템 환경 구성


sudo apt update
sudo apt install python3 python3-pip -y
python3 --version


### Poetry 설치


pip3 install poetry
poetry --version


---

### 2️⃣ 프로젝트 설치


git clone [레포지토리 주소]
cd Crawling-batch
poetry install


Playwright 설치


poetry run playwright install --with-deps chromium


---

### 3️⃣ 환경 변수 설정


cp .env.example .env.prod
chmod 600 .env.prod


.env.prod


APP_ENV=prod
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=운영비밀번호
DB_NAME=crawling
CRON_INTERVAL_MINUTES=120


---

### 4️⃣ DB 마이그레이션


mysql -u root -p < sql/V1__init_schema.sql
mysql -u root -p crawling < sql/V2__add_deal_detail_columns.sql
mysql -u root -p crawling < sql/V3__add_status_column.sql


---

### 5️⃣ 서버 실행

포그라운드


APP_ENV=prod poetry run crawling-batch


백그라운드


nohup APP_ENV=prod poetry run crawling-batch > /dev/null 2>&1 &


---

## 🔎 운영 관리

프로세스 확인


ps aux | grep crawling


프로세스 종료


kill $(ps aux | grep crawling-batch | grep -v grep | awk '{print $2}')


---

## 📝 관리자 참고사항

키워드 관리


src/crawling_batch/config/keywords.py


로그 확인


logs/crawling_YYYY-MM-DD.log


실시간 로그


tail -f logs/crawling_*.log


- 콘솔 : INFO 이상 로그  
- 파일 : 7일 보관 후 자동 삭제
