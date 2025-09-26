FROM python:3.10-slim
WORKDIR /app

# Cài deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code + model
COPY app ./app
COPY model ./model

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host","0.0.0.0","--port","8000"]
