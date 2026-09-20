FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --uid 10001 --create-home pol && mkdir -p /app/data /app/staticfiles && chown -R pol:pol /app
USER pol
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
