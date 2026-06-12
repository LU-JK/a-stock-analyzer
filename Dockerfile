FROM python:3.12-slim

# 时区设为中国
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目
COPY backend/ ./backend/
COPY web/ ./web/

WORKDIR /app/backend

# 云平台通过 PORT 环境变量指定端口
CMD sh -c 'python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}'
