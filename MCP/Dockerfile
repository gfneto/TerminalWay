FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY terminalway ./terminalway
RUN useradd --uid 10001 --create-home appuser
USER appuser
EXPOSE 8000
CMD ["python", "-m", "terminalway.mcp_server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
