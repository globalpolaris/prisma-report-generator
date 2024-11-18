FROM python:3.9-slim

workdir /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/1 Home.py", "--server.headless=true", "--server.port=8501"]