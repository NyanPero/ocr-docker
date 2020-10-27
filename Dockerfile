FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt /app

RUN apt update -y && \
    apt install git -y && \
    apt install libopencv-dev -y && \
    apt install whois -y && \
    apt install tesseract-ocr-jpn -y && \
    pip install --no-cache-dir -r requirements.txt && rm requirements.txt

COPY /src /app

CMD ["python", "/app/main.py", "-d", "/app/domain.txt", "-p", "/app/phone.txt", "-j", "/app/*.jsonl", "-o", "/app/out/", "-s", "600000"]
