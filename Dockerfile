# TianYi LangChain App - 一体式 Docker 镜像
# 包含 FastAPI 后端 + Jinja2 前端 + LangChain API

FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml uv.lock* ./

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi uvicorn[standard] \
        sqlmodel bcrypt pyjwt \
        python-multipart python-dotenv \
        jinja2 aiofiles itsdangerous \
        pydantic email-validator \
        httptools \
        resend \
        langchain langchain-community langchain-core \
        langchain-deepseek langchain-postgres \
        psycopg2-binary \
        sentence-transformers

# 复制应用代码
COPY main.py .
COPY routers/ routers/
COPY utils/ utils/
COPY templates/ templates/
COPY static/ static/
COPY exceptions/ exceptions/
COPY .env ./

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read())" || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
