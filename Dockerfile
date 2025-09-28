# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt 
COPY requirements.txt .

# Install pip and Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY model ./model
COPY healthcheck.py .

# Expose port
EXPOSE 8086

# Add HEALTHCHECK using Python script
HEALTHCHECK --interval=10s --timeout=3s --start-period=40s --retries=5 \
  CMD python healthcheck.py || exit 1

# Command to run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8086"]
