# =============================================================================
# Dockerfile - Crawling-batch 배포용
# Ubuntu 서버에서: docker build -t crawling-batch .
#                  docker run -d --name crawling-batch --env-file .env.prod crawling-batch
# =============================================================================

FROM python:3.14-slim

# Playwright 브라우저에 필요한 시스템 패키지
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Poetry 설치
RUN pip install poetry

# 의존성 먼저 설치 (캐싱 활용 - 소스 바뀌어도 의존성 안 바뀌면 재설치 안 함)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Playwright 브라우저 설치
RUN poetry run playwright install chromium

# 소스 복사
COPY src/ src/

# 패키지 설치 (소스 포함)
RUN poetry install

# 로그 디렉토리
RUN mkdir -p logs

CMD ["poetry", "run", "crawling-batch"]
