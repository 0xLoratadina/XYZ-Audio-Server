# ────────────────────────────────────────────────
# RadioStatus – Dockerfile (Ubuntu 22.04 + Python 3.13.2)
# ────────────────────────────────────────────────
FROM ubuntu:22.04 AS build

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSION=3.13.2

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential wget curl ca-certificates \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    libncursesw5-dev libffi-dev liblzma-dev tk-dev uuid-dev libgdbm-dev \
    libxml2-dev libxmlsec1-dev libsndfile1 ffmpeg \
 && wget -q https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \
 && tar -xzf Python-${PYTHON_VERSION}.tgz

WORKDIR /Python-${PYTHON_VERSION}

RUN ./configure --enable-optimizations --with-lto \
 && make -j$(nproc) \
 && make altinstall        # instala python3.13 y pip3.13

# ─── Runtime ────────────────────────────────────
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/bin/python3.13 /usr/local/bin/python3.13
COPY --from=build /usr/local/bin/pip3.13    /usr/local/bin/pip3.13
COPY --from=build /usr/local/lib/python3.13  /usr/local/lib/python3.13
COPY --from=build /usr/local/include/python3.13 /usr/local/include/python3.13
COPY --from=build /usr/local/lib/pkgconfig /usr/local/lib/pkgconfig

ENV PATH="/usr/local/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip3.13 install --upgrade pip \
 && pip3.13 install gunicorn \
 && pip3.13 install -r requirements.txt

COPY . .

EXPOSE 20000

CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:20000", "run:app"]
