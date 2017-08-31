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
RUN coverage run --branch -m unittest discover -f
RUN coverage report -m --skip-covered --fail-under=75
ENV DESTALINATOR_LOG_LEVEL WARNING
CMD python scheduler.py

### Coverage HTML report
## Uncomment these:
# RUN coverage html --skip-covered
# CMD python -m http.server 80
## Then run: docker run -it -p 8080:80 destalinator
## And open: http://localhost:8080/htmlcov/
