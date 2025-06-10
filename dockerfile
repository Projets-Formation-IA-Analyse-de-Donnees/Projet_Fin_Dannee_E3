FROM python:3.10-slim

WORKDIR /code

COPY . /code/

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "run.py"]  
