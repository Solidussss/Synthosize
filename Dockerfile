FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 STUDIO_DATA_DIR=/data PORT=8080
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg gosu && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 studio && useradd --uid 10001 --gid studio --create-home studio
WORKDIR /app
COPY requirements.txt requirements-hosted.txt ./
RUN pip install --no-cache-dir -r requirements-hosted.txt
COPY engine ./engine
COPY ui ./ui
COPY examples ./examples
COPY docker-entrypoint.sh ./
RUN mkdir -p /data && chown studio:studio /data && chmod +x docker-entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "-m", "engine.hosted"]
