FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ /app/shared/
COPY api-gateway/ /app/api-gateway/
CMD ["uvicorn", "api-gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
