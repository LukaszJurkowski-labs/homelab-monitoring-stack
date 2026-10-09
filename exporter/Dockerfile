# 1. Warstwa bazowa (cache'd, nie zmienia się często)
FROM python:3.11-slim

# 2. Katalog roboczy
WORKDIR /app

# 3. Instalacja zależności (cache'd — zmieni się tylko, gdy zmienisz requirements)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kod aplikacji (tę warstwę cache'd jest mniej ważny)
COPY main.py .

# 5. Port (informacja meta, nie robi nic runtime)
EXPOSE 8000

# 6. Start kontenera
CMD ["python", "main.py"]
