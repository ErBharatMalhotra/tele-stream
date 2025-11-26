FROM debian:latest

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv ffmpeg && \
    apt-get clean

WORKDIR /app

COPY . .

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python3", "main.py"]
