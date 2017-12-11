FROM python:2.7-alpine
WORKDIR /destalinator
ADD bin/install bin/
ADD build-requirements.txt .
ADD requirements.txt .
RUN ./bin/install
ADD *.py ./
ADD *.txt ./
ADD *.md ./
ADD Procfile .
ADD LICENSE .
ADD configuration.yaml .
ADD utils/*.py utils/
ADD tests/* tests/
ADD bin/test bin/
RUN ./bin/test
ENV DESTALINATOR_LOG_LEVEL WARNING
CMD python scheduler.py
