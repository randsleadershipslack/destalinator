FROM python:3.7-buster

ENV DESTALINATOR_LOG_LEVEL WARNING

WORKDIR /destalinator

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "scheduler.py"]
