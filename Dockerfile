FROM python:3.6
WORKDIR /destalinator
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD *.py ./
ADD *.txt ./
ADD *.md ./
ADD Procfile .
ADD LICENSE .
ADD configuration.yaml .
ADD utils/*.py utils/
ENV DESTALINATOR_LOG_LEVEL WARNING
CMD python scheduler.py
