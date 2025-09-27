FROM python:3.10-slim

WORKDIR /app

# Cài system deps cho sonar-scanner
RUN apt-get update && apt-get install -y wget unzip curl \
    && rm -rf /var/lib/apt/lists/*

# Cài sonar-scanner CLI
RUN wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip \
    && unzip sonar-scanner-cli-*.zip -d /opt \
    && ln -s /opt/sonar-scanner-*/bin/sonar-scanner /usr/local/bin/sonar-scanner \
    && rm sonar-scanner-cli-*.zip

# Copy requirements + cài Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code + model
COPY app ./app
COPY model ./model

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host","0.0.0.0","--port","8000"]
