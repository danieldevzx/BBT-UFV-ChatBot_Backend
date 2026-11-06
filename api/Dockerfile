FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O chatbot.db fica no volume /data. Na primeira subida, se o volume estiver
# vazio, copia o banco populado do projeto; depois só aplica migrações.
ENV DB_PATH=/data/chatbot.db FLASK_APP=run.py
VOLUME ["/data"]
EXPOSE 5000

CMD ["sh", "-c", "[ -f \"$DB_PATH\" ] || cp db/chatbot.db \"$DB_PATH\"; flask db upgrade && exec gunicorn --workers 1 --threads 8 --bind 0.0.0.0:5000 run:app"]
