
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y procps
RUN apt-get update && apt-get install -y libgl1
RUN apt-get update && apt-get install -y libglib2.0-0

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/media/cover_images

EXPOSE 8000
VOLUME ["/app/db", "/app/media", "/app/logs"]
RUN chmod 777 start.sh
CMD ["./start.sh"]
