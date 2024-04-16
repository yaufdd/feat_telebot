FROM python

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir telebot redis requests

ENV TELEBOT_TOKEN=7128882313:AAHlbCt3AtnbkYpzqWinVYkH71GqKOT6n1k
ENV REDIS_HOST=redis

CMD ["python", "main.py"]

