FROM python:3.11-slim
RUN pip install --no-cache-dir psycopg2-binary==2.9.10
WORKDIR /app
COPY generer_donnees.py .
CMD ["python", "generer_donnees.py"]
