FROM python:3.9-slim

LABEL maintainer="Lee M. Lwando <leemlwando@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/leemlwando/ns8-mail-webhooks"
LABEL org.opencontainers.image.description="NethServer 8 Mail Webhooks Module"
LABEL org.opencontainers.image.author="Lee M. Lwando"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY imageroot/pypkg/mailwebhook/ /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
