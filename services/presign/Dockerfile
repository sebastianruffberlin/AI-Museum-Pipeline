FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY presign_app.py .
EXPOSE 8082
CMD ["uvicorn", "presign_app:app", "--host", "0.0.0.0", "--port", "8082"]
