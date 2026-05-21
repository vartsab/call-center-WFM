FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY docs ./docs

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "app/streamlit/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
