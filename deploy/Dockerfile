FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .
ENV MUSEUM_PIPELINE_HOME=/app
ENTRYPOINT ["museum-pipeline"]
CMD ["validate-config"]
