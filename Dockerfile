FROM debian:latest

RUN apt-get update && \
    apt-get install -y python3 python3-pip ffmpeg && \
    apt-get clean

WORKDIR /app
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]
