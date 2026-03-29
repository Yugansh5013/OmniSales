FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ /app/shared/
COPY agents/spy/ /app/agents/spy/
CMD ["uvicorn", "agents.spy.server:app", "--host", "0.0.0.0", "--port", "8080"]
