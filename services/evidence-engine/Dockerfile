FROM python:3.12-slim

# Create unprivileged non-root user (uid: 10001, gid: 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app

# Ensure proper permissions
RUN chown -R appuser:appgroup /app

# Drop to non-root user
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import httpx; resp = httpx.get('http://127.0.0.1:8000/health'); exit(0 if resp.status_code == 200 else 1)"

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
