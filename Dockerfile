FROM debian:latest

# Install system packages including python and ffmpeg
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv ffmpeg && \
    apt-get clean

WORKDIR /app

COPY . .

# Create & use virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python packages inside virtual environment
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python3", "main.py"]
