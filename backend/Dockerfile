FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
COPY . .
RUN useradd -r anomaly && chown -R anomaly:anomaly /app
USER anomaly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
