# Base image: Python 3.10 slim
FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy requirements.txt trước để tận dụng cache
COPY requirements.txt .

# Cài đặt pip và dependencies Python
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy code ứng dụng
COPY app ./app
COPY model ./model
COPY healthcheck.py .

# Expose cổng
EXPOSE 8086

# Thêm HEALTHCHECK dùng script Python
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python healthcheck.py || exit 1

# Lệnh khởi động FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8086"]
