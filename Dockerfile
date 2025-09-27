
# Build dependencies
FROM python:3.10-slim AS builder

# Đặt biến môi trường để apt-get chạy không tương tác
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt các gói hệ thống cần thiết cho việc build Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements.txt trước để tận dụng cache
COPY requirements.txt .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements.txt



# Final image (smaller)
FROM python:3.10-slim

# Đặt biến môi trường để apt-get chạy không tương tác
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt các gói hệ thống tối thiểu (nếu cần)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép dependencies đã cài từ stage builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Sao chép mã nguồn dự án
COPY . .

# Khai báo command để chạy ứng dụng
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
