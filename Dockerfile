FROM python:3.12-slim

ENV TZ=Asia/Tehran
ENV PYTHONUNBUFFERED=1

# Install build tools + graphics libraries + libraqm (for RTL text)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    tzdata \
    fontconfig \
    libfreetype6 \
    libfreetype6-dev \
    libharfbuzz-dev \
    libraqm-dev \
    libraqm0 \
    libfribidi-dev \
    fonts-noto-core \
    fonts-noto-extra \
    fonts-dejavu \
    libjpeg62-turbo \
    libjpeg62-turbo-dev \
    libpng16-16 \
    libpng-dev \
    ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir arabic-reshaper python-bidi && \
    pip install --no-cache-dir --force-reinstall --no-binary=Pillow Pillow

COPY . .
