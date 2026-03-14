🍾 Crawling-batch (Casky 앱 연동 주류 핫딜 크롤러)Casky 서비스에 제공되는 주류 핫딜 정보를 수집하기 위한 자동화 크롤링 배치(Batch) 서버입니다. 지정된 스케줄에 따라 각 커뮤니티와 주류 전문 사이트의 게시글을 크롤링하고 필터링하여 데이터베이스에 적재합니다.🛠 환경 요구사항 (Prerequisites)항목버전비고LanguagePython 3.14+Package ManagerPoetry 2.3.2+의존성 관리DatabaseMariaDB 10.11+Data 스토리지 분리 환경 권장OSUbuntu 22.04+ / Windows 11📦 주요 설치 패키지 (Tech Stack)패키지버전용도playwright1.58.0브라우저 크롤링 (JS 동적 렌더링 처리)playwright-stealth2.0.2사이트 봇 감지 우회beautifulsoup44.14.3HTML 파싱 및 DOM 탐색requests2.32.5HTTP API 요청pymysql1.1.2MariaDB 연결 및 쿼리 실행python-dotenv1.2.2.env 환경변수 로딩apscheduler3.11.2크롤링 주기 실행 스케줄러loguru0.7.3파일 및 콘솔 로깅pydantic / pydantic-settings2.x데이터 모델 검증 및 환경변수 매핑📁 프로젝트 구조 (Project Structure)Plaintextsrc/crawling_batch/
 ├── config/
 │   ├── settings.py        # 환경변수 설정 (.env 로딩)
 │   ├── database.py        # MariaDB 연결 및 세션 관리
 │   └── keywords.py        # ★ 주류 필터 키워드 관리 ★
 ├── crawler/
 │   ├── base.py            # 크롤러 공통 부모 (필터/저장/만료처리 로직)
 │   ├── arca.py            # 아카라이브 핫딜 크롤러
 │   ├── ppomppu.py         # 뽐뿌 핫딜 크롤러
 │   ├── ruliweb.py         # 루리웹 핫딜 크롤러 (상세페이지 링크 추출)
 │   └── wineandmore.py     # 와인앤모어 프로모션 크롤러
 ├── model/
 │   └── hotdeal.py         # HotDeal 데이터 DTO/Model
 └── main.py                # 엔트리포인트 (스케줄러 실행)
🕸 크롤링 대상 및 스케줄 (Crawling Sources)타겟 사이트실행 주기필터링 조건아카라이브 핫딜2시간 간격당일 게시물 + 주류 관련 키워드뽐뿌 핫딜2시간 간격당일 게시물 + 주류 관련 키워드루리웹 핫딜2시간 간격당일 게시물 + 주류 관련 키워드 + 상세 링크 추출와인앤모어1일 1회 (09:00)주류 전문 몰 전체 프로모션🚀 배포 및 실행 가이드 (Deployment)가비아 클라우드 등 Ubuntu 서버 환경을 기준으로 한 배포 방법입니다.1. 시스템 환경 구성Bash# Python 설치 (3.14+ 확인)
sudo apt update
sudo apt install python3 python3-pip -y
python3 --version  

# Poetry 설치
pip3 install poetry
poetry --version
2. 프로젝트 셋업 및 의존성 설치Bash# 소스 클론 및 디렉토리 이동
git clone [레포지토리 주소]
cd Crawling-batch

# 파이썬 패키지 설치
poetry install

# Playwright 브라우저 및 시스템 의존성 설치 (Chromium)
poetry run playwright install --with-deps chromium
3. 환경 변수 및 DB 설정cp .env.example .env.prod 명령어로 파일을 복사한 뒤, 아래와 같이 운영 환경에 맞게 수정합니다. (chmod 600 .env.prod 권장)Ini, TOMLAPP_ENV=prod
DB_HOST=127.0.0.1      # Data 스토리지를 별도 분리한 경우 해당 IP 입력
DB_PORT=3306
DB_USER=root
DB_PASSWORD=운영비밀번호
DB_NAME=crawling
CRON_INTERVAL_MINUTES=120
데이터베이스 스키마 마이그레이션을 진행합니다.Bashmysql -u root -p < sql/V1__init_schema.sql
mysql -u root -p crawling < sql/V2__add_deal_detail_columns.sql
mysql -u root -p crawling < sql/V3__add_status_column.sql
4. 서버 실행 및 관리Bash# 포그라운드 실행 (테스트 및 디버깅용)
APP_ENV=prod poetry run crawling-batch

# 백그라운드 무중단 실행 (운영용)
nohup APP_ENV=prod poetry run crawling-batch > /dev/null 2>&1 &

# 실행 중인 프로세스 확인
ps aux | grep crawling

# 백그라운드 프로세스 종료
kill $(ps aux | grep crawling-batch | grep -v grep | awk '{print $2}')
📝 관리자 참고 사항 (Notes)키워드 관리: 크롤링 필터링에 사용되는 주류 키워드를 추가하거나 수정하려면 src/crawling_batch/config/keywords.py 파일을 수정하세요.로그 확인: * 실행 로그는 logs/crawling_YYYY-MM-DD.log 형태로 저장됩니다. (tail -f logs/crawling_*.log로 실시간 확인 가능)콘솔에는 INFO 레벨 이상의 로그가 출력되며, 로그 파일은 7일간 보관 후 자동 삭제되도록 설정되어 있습니다.
