FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ /app/shared/
COPY mcp-servers/crm/server.py /app/server.py
CMD ["python", "server.py"]
