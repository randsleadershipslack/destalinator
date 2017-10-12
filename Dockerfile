FROM python:alpine3.6
WORKDIR /destalinator
ADD bin/* bin/
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
RUN ./bin/test
ENV DESTALINATOR_LOG_LEVEL WARNING
CMD python scheduler.py
