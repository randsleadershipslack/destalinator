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
RUN flake8 --ignore=E501
# Skip tests/test_destalinator.py due to heavy mocking. See https://github.com/jendrikseipp/vulture/issues/95
# Skip utils/slack_logging.py due to implementing Handler#emit but never calling directly
RUN vulture . --exclude=tests/test_destalinator.py,utils/slack_logging.py
RUN coverage run --branch --source=. -m unittest discover -f
RUN coverage report -m --skip-covered --fail-under=71
ENV DESTALINATOR_LOG_LEVEL WARNING
CMD python scheduler.py

### Coverage HTML report
## Uncomment these:
# RUN coverage html --skip-covered
# CMD python -m http.server 80
## Then run: docker run -it -p 8080:80 destalinator
## And open: http://localhost:8080/htmlcov/
