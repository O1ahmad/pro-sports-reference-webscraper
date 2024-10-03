FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/

# Leverage Docker's caching while installing dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENTRYPOINT ["python", "nba/main.py"]
