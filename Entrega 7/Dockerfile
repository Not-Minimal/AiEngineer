FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY data/ data/
COPY scripts/ scripts/

# La misma imagen sirve para la API y el worker; docker-compose.yml elige el comando.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
