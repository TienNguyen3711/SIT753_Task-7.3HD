# Base image: Python 3.10 slim
FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy requirements.txt trước để tận dụng cache
COPY requirements.txt .

# Cài đặt pip và dependencies Python
# Không cần build-essential nếu requirements chỉ có numpy/pandas/sklearn (đã có wheel)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy code ứng dụng
COPY app ./app
COPY model ./model
COPY healthcheck.py .

# Expose cổng
EXPOSE 8000

# Lệnh khởi động FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
