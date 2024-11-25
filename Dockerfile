FROM python:3.10-slim

RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["scalesops", "main.py"]