FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --default-timeout=180 --retries=10 \
    torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=180 --retries=10 -r requirements.txt

COPY app/ app/
COPY migrations/ migrations/
COPY app_ui.py .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]