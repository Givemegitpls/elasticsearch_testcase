FROM python:3.12.8

COPY requirements.txt .

RUN pip install -r requirements.txt

WORKDIR /var/lib/python_project

VOLUME /var/lib/python_project

COPY main.py /var/lib/python_project

CMD ["python",  "main.py"]


