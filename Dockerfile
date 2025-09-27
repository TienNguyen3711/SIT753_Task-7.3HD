FROM python:3.10-slim

WORKDIR /app

# Thêm dòng này để apt-get chạy không tương tác
ENV DEBIAN_FRONTEND=noninteractive

# Cài deps hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tận dụng cache
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy code + model
COPY app ./app
COPY model ./model
COPY test ./test
COPY healthcheck.py .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["python", "healthcheck.py"]
