# Sử dụng base image Python 3.10 slim
FROM python:3.10-slim

# Đặt thư mục làm việc chính
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt trước để tận dụng Docker cache
COPY requirements.txt .

# Nâng cấp pip và cài đặt các thư viện Python
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy tất cả các file cần thiết vào thư mục làm việc
# Lưu ý: Các thư mục này sẽ nằm ở /app/app và /app/model
COPY app ./app
COPY model ./model
COPY healthcheck.py .

# Mở cổng cho ứng dụng
EXPOSE 8000

# Lệnh mặc định để chạy ứng dụng khi container khởi động
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]