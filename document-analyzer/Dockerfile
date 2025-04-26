FROM python:3.11-slim

LABEL maintainer="Fengxin Dai"

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]