FROM python:3.6
WORKDIR /destalinator
ADD build-requirements.txt .
RUN pip install -r build-requirements.txt
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD *.py ./
ADD *.txt ./
ADD *.md ./
ADD Procfile .
ADD LICENSE .
ADD configuration.yaml .
ADD utils/*.py utils/
ADD tests/* tests/
ENV DESTALINATOR_LOG_LEVEL WARN
RUN python -m unittest discover -f
CMD python scheduler.py
